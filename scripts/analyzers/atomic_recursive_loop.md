Amazing context — this is perfect. Below is a **drop-in spec** (math + protocol flow + code integration plan) tailored to your analyzer so you can switch from the “23-loop” path to the **one-shot Instadapp route** on the way in, and the **cheap flash-assisted partial unwind** on the way out.

---

# ENTRY (one-shot, Instadapp, 0-bps flash if possible)

## Goal

With equity **E** (USD) and target **LTV λ = 0.93**, open in **one atomic tx**:

* Supply **weETH** collateral worth **S = E + F**
* Borrow **WETH** debt **B = F**
* Repay flash with **B**, leaving net long ≈ **E** in ETH terms (delta-neutral once your CEX short is live)

## Sizing (no micro-loops)

[
F=\frac{λ}{1-λ}E\qquad S=E+F\qquad B=F
]
For **E=$100,000**, **λ=0.93**:

* (F = 0.93/0.07 \cdot 100{,}000 = $1{,}328{,}571.43)
* (S = 1{,}428{,}571.43)
* (B = 1{,}328{,}571.43)
  (Use a small buffer: set (B = \min(F,;λ\cdot S - \delta)) with (\delta\sim 0.25%\cdot S))

## Atomic path (Instadapp connectors)

Inside a single transaction (your account = DSA / Safe as sender):

1. **Flash-borrow WETH = F** (via Instadapp’s flash aggregator; route to **Balancer/Morpho** for 0 bps when liquid, else Aave at ~5 bps).
2. **Unwrap WETH→ETH** if Ether.fi requires ETH (skip if you can feed WETH to their router).
3. **Stake at Ether.fi** → receive **eETH**, **wrap to weETH**.
4. **Aave `supplyWithPermit(weETH)`** (collateral enabled).
5. **Aave `borrow(WETH, B)`** (variable; eMode ETH-correlated bucket).
6. **Repay flash** with the borrowed **WETH**.
7. **Assert post-tx**: HF ≥ threshold (e.g., 1.10+), LTV ≤ λ, mint rate bounds, oracle sanity.

**Fees at entry**

* **Flash fee φ**: 0 bps (Balancer/Morpho) or ~5 bps (Aave) on **F** (one-off).
* **Gas**: ~**0.7–1.2M** gas for the whole recipe (vs ~15M+ for 20+ micro loops).
* **No DEX swap** on entry → no platform swap fee.

**Edge checks to code**

* Flash liquidity for WETH ≥ F.
* Aave borrow cap headroom ≥ B.
* eMode active & weETH params (LTV=0.93, LT).
* Mint rate tolerance on Ether.fi (ρₛ bounds).

---

# UNWIND / PARTIAL CASH-OUT (cheapest atomic path)

You want to free **cash** (e.g., because ETH rose +20%) while maintaining (roughly) the same LTV afterward and topping up your CEX short P&L.

Let **p** be the fraction of **current debt D** you want to repay (e.g., p=0.20). Then **R = p·D** is the **repay slice** (WETH). To keep LTV ~unchanged after the repay:

[
W_{$} = \frac{R}{λ}\quad (\text{USD value of weETH to withdraw})
]

**One atomic tx (flash-assisted, includes a swap)**

1. **Flash-borrow WETH = R** (0 bps when possible).
2. **Aave `repay(WETH, R)`** → new debt (D' = D - R).
3. **Aave `withdraw(weETH, W\$/oracle)`** to unlock collateral worth (W_{$}=R/λ).
4. **Swap inside the same tx** (must be on-chain, not CoW):

   * **Leg A (flash repay)**: swap *just enough* of the withdrawn **weETH** → **WETH** to net **R** (account for pool fee & slippage).
   * **Leg B (cash)**: swap the **excess** to **USDT** (this is your free cash, ≈ the equity slice you’re lifting).
5. **Repay flash** with **R** WETH from Leg A.
6. **Post-checks**: HF ≥ threshold, LTV ≤ target, min-out checks satisfied.

**Why a swap is required here**
Your flash is **WETH**, collateral is **weETH**. To repay the flash in-tx you must produce **WETH**; hence the swap occurs **before** flash repayment, **inside the tx**.

**Where to swap (no platform fee)**

* **Use Instadapp** + call **1inch Aggregation Router / Uniswap v3 / Curve** directly from your recipe → you pay only **pool fee + slippage** (no DeFi Saver swap fee).
* **Do not** use CoW inside this tx (off-chain solver submits the tx; you can’t bundle it into *your* atomic transaction).

**DEX fee modeling (backtest)**

* **Curve** weETH/WETH pool: use its pool fee (often very low) + slippage.
* **Uniswap v3**: choose the best tier (0.01/0.05/0.30/1.00%).
* **1inch**: treat as routing over underlying pools; no extra protocol fee by default.
  Include a **slippage_bps** param and a **dex_fee_bps_by_pair** map.

---

# WHAT TO ADD / CHANGE IN YOUR ANALYZER

## 1) New config fields

```python
@dataclass
class StrategyConfig:
    use_flash_one_shot: bool = True
    flash_source: str = "BALANCER_OR_MORPHO"  # "AAVE" fallback
    flash_fee_bps: float = 0.0  # 0.0 if Balancer/Morpho route filled; else ~5.0
    entry_hf_min: float = 1.10
    unwind_hf_min: float = 1.10
    ltv_target: float = 0.93     # same as max_ltv but keep both if you want a buffer
    ltv_buffer_bps: float = 25.0 # δ buffer: 25 bps of S
    swap_slippage_bps: float = 5.0
    dex_fee_bps_weeth_weth: float = 3.0   # example; set per-pool or size-aware
    dex_fee_bps_weth_usdt: float = 3.0
```

## 2) Replace the 23-loop entry with a one-shot entry

Add a new method alongside `_execute_leverage_loop_usd`:

```python
def _execute_leverage_one_shot_usd(self, t0: pd.Timestamp, equity_usd: float, eth_price: float) -> Dict:
    λ = self.config.ltv_target
    E = equity_usd
    F = (λ/(1-λ)) * E
    S = E + F
    δ = (self.config.ltv_buffer_bps / 1e4) * S
    B = min(F, λ*S - δ)

    # Gas & flash fee
    gas_entry_usd = self._get_gas_cost_usd(t0, 'ATOMIC_ENTRY', eth_price)  # add row to gas model
    flash_fee_usd = (self.config.flash_fee_bps/1e4) * F

    # Log atomic events (single tx)
    self._log_event(t0, 'FLASH_BORROW', 'INSTADAPP', 'WETH', F, fee_bps=self.config.flash_fee_bps)
    self._log_event(t0, 'STAKE_DEPOSIT', 'ETHERFI', 'ETH', S, output_token='weETH',
                    amount_out=S/eth_price/self.data['oracle_prices'].loc[
                        self.data['oracle_prices'].index.asof(t0),'oracle_price_eth'
                    ])
    self._log_event(t0, 'COLLATERAL_SUPPLIED', 'AAVE', 'weETH', S)
    self._log_event(t0, 'LOAN_CREATED', 'AAVE', 'WETH', B, ltv=λ)
    self._log_event(t0, 'FLASH_REPAID', 'INSTADAPP', 'WETH', B, fee_usd=flash_fee_usd)
    self._log_event(t0, 'GAS_FEE_PAID', 'ETHEREUM', 'ETH', gas_entry_usd/eth_price,
                    fee_type='atomic_entry', fee_usd=gas_entry_usd)

    # State (in WETH terms)
    weeth_price = self._get_rates_at_timestamp(t0)['weeth_price']
    weeth_units = S / eth_price / weeth_price
    weth_debt  = B / eth_price

    # Health Factor
    LT = self.config.liquidation_threshold  # e.g., 0.95 for weETH eMode
    collateral_weth = weeth_units * weeth_price
    hf = (LT * collateral_weth) / weth_debt

    return {
        'timestamp': t0,
        'iteration_count': 1,
        'weeth_collateral': weeth_units,
        'weth_debt': weth_debt,
        'collateral_value_weth': collateral_weth,
        'net_position_weth': collateral_weth - weth_debt,
        'net_position_usd': (collateral_weth - weth_debt) * eth_price,
        'long_eth_exposure': collateral_weth - weth_debt,
        'health_factor': hf,
        'leverage_multiplier': collateral_weth / (E/eth_price),
        'total_gas_costs_usd': gas_entry_usd,
        'flash_fee_usd': flash_fee_usd,
        'weeth_price': weeth_price,
        'venue_positions': {...}
    }
```

Then, in `run_analysis()`, **replace**:

```python
long_position = self._execute_leverage_loop_usd(t0, long_capital_net, eth_price_spot)
```

with

```python
if self.config.use_flash_one_shot:
    long_position = self._execute_leverage_one_shot_usd(t0, long_capital_net, eth_price_spot)
else:
    long_position = self._execute_leverage_loop_usd(t0, long_capital_net, eth_price_spot)
```

> Also add a **new gas row** in your gas CSV for `ATOMIC_ENTRY`, and similarly `ATOMIC_DELEVERAGE` below (use your historical gwei → cost model; default to 0.9M and 0.8M gas placeholders if you need constants).

## 3) Add a flash-assisted partial deleverage method

```python
def _deleverage_flash_atomic(self, t: pd.Timestamp, repay_fraction: float,
                             eth_price: float, want_usdt_usd: Optional[float]=None) -> Dict:
    # Current state
    D = self.current_weth_debt()             # in WETH units
    S_units = self.current_weeth_units()
    weeth_price = self._get_rates_at_timestamp(t)['weeth_price']

    # Slice to repay
    R_weth = repay_fraction * D              # units of WETH
    R_usd = R_weth * eth_price
    λ = self.config.ltv_target
    W_usd = R_usd / λ                        # collateral USD to withdraw
    W_weeth = (W_usd / eth_price) / weeth_price

    # Flash & gas
    flash_fee_usd = (self.config.flash_fee_bps/1e4) * R_usd
    gas_unwind_usd = self._get_gas_cost_usd(t, 'ATOMIC_DELEVERAGE', eth_price)

    # Log
    self._log_event(t,'FLASH_BORROW','INSTADAPP','WETH',R_usd,fee_bps=self.config.flash_fee_bps)
    self._log_event(t,'LOAN_REPAID','AAVE','WETH',R_usd)
    self._log_event(t,'COLLATERAL_WITHDRAWN','AAVE','weETH',W_weeth,
                    usd_value=W_usd, weeth_price=weeth_price)

    # Swaps inside tx (no platform fee if you call 1inch/Uni/Curve directly)
    dex_fee_a = self.config.dex_fee_bps_weeth_weth/1e4
    min_weth_for_flash = R_weth * (1 + self.config.swap_slippage_bps/1e4)
    weth_from_legA = R_weth * (1 + dex_fee_a)  # oversimplified; your model can be precise
    self._log_event(t,'SWAP_EXECUTED','DEX','weETH',W_weeth,
                    legs=[{'pair':'weETH/WETH','fee_bps':self.config.dex_fee_bps_weeth_weth}])

    self._log_event(t,'FLASH_REPAID','INSTADAPP','WETH',R_usd, fee_usd=flash_fee_usd)

    # Excess to USDT
    excess_weth = max(0.0, (W_weeth*weeth_price) - R_weth)  # in WETH units (approx)
    excess_usd = excess_weth * eth_price
    if want_usdt_usd is None:
        want_usdt_usd = excess_usd
    take_usd = min(excess_usd, want_usdt_usd)
    if take_usd > 0:
        dex_fee_b = self.config.dex_fee_bps_weth_usdt/1e4
        self._log_event(t,'SWAP_EXECUTED','DEX','WETH',take_usd/eth_price,
                        legs=[{'pair':'WETH/USDT','fee_bps':self.config.dex_fee_bps_weth_usdt}],
                        amount_out_usd=take_usd*(1-dex_fee_b))

    self._log_event(t,'GAS_FEE_PAID','ETHEREUM','ETH',gas_unwind_usd/eth_price,
                    fee_type='atomic_deleverage', fee_usd=gas_unwind_usd)

    # Update internal state (reduce debt, reduce collateral)
    self.decrease_weth_debt(R_weth)
    self.decrease_weeth_collateral(W_weeth)

    # Recompute HF
    LT = self.config.liquidation_threshold
    new_collateral_weth = self.current_weeth_units()*weeth_price
    new_debt_weth = self.current_weth_debt()
    hf = (LT * new_collateral_weth) / max(new_debt_weth, 1e-12)

    return {
        'timestamp': t,
        'repaid_weth': R_weth,
        'withdrawn_weeth': W_weeth,
        'freed_usdt_usd': take_usd*(1 - self.config.dex_fee_bps_weth_usdt/1e4),
        'flash_fee_usd': flash_fee_usd,
        'gas_unwind_usd': gas_unwind_usd,
        'post_hf': hf
    }
```

> Use this method when you detect “equity up X%” rebalances (your rebalance triggers). Pass `repay_fraction ≈ X%` to free similar %-of-equity in cash. Add safety: withdraw slightly **less** than (R/λ) to lower LTV post-tx.

## 4) Update your **gas price table**

Add two synthetic transaction types with your preferred median gas assumptions:

* `ATOMIC_ENTRY`: 0.9M gas baseline
* `ATOMIC_DELEVERAGE`: 0.8M gas baseline
  (Scale by gwei × ETHUSD and your `gas_cost_multiplier` as you do now.)

## 5) Costs & logging you’ll now capture

* **Entry**: `flash_fee_usd` (usually 0), `total_gas_costs_usd` for `ATOMIC_ENTRY`.
* **Unwind**: `flash_fee_usd` (usually 0), `gas_unwind_usd` for `ATOMIC_DELEVERAGE`, plus **DEX fees + slippage** on the two swap legs (model with `dex_fee_bps_*` + `swap_slippage_bps`).

## 6) Health Factor & buffers

* Keep **HF_min** guards on both entry and unwind.
* Keep a **buffer δ** under LTV 0.93 at entry and withdraw slightly less than (R/λ) on unwind to avoid creeping up to limits due to pricing/rounding.

---

# QUICK CHECKS FOR YOUR $100k / 0.93 EXAMPLE

* **Entry**: E=100k → F≈1.3286m → S≈1.4286m; set B≈min(F, 0.93·S − δ). LTV ≈ 0.93 with δ buffer, HF computed with LT (e.g., 0.95). Net delta long ≈ E.
* **Unwind 20%**: D is current debt; R=0.20·D; withdraw (W_{$}=R/0.93). Swap a slice of weETH→WETH to repay **R**, swap the **excess** to **USDT** (~$20k target), repay flash, done — LTV ~unchanged.

---

# WHY INSTADAPP FOR “LOW/NO CODE”

* Their **Flashloan Aggregator** picks Balancer/Morpho/Aave under the hood.
* You can call **1inch/Uni/Curve** directly from your DSA using their connectors (no platform swap fee).
* You avoid writing flash-loan plumbing, permits, and Aave connector glue yourself.

---

If you want, I can turn the snippets above into **actual small Python hooks** in your class (function skeletons that call your existing logging, pricing, and gas models), but the pieces you need are all here:

* **math (F, B, W$)**,
* **atomic sequences** (entry & unwind),
* **config knobs** (flash, fees, slippage),
* **state updates + events**,
* **HF/LTV safety**.
