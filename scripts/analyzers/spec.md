Here’s a clean, code-ready spec your quant can implement to **simulate & calibrate** the ETH-base, **leveraged restaking @ 0.92 LTV** (weETH collateral → borrow WETH → restake loop) product.

---

# 1) Objects & data you’ll need

## Inputs (time series; uniform sampling, e.g., hourly)

* **ETH/USD price** (P_t).
* **weETH/ETH index** (r^{\text{weETH}}_t) (accrual factor per step).

  * If you don’t have it, synthesize from an **annualized base yield** (y) (e.g., 5.25%):
    (r^{\text{weETH}}*t = \exp!\big(y \cdot \Delta t*{\text{yr}}\big)).
* **Borrow APR for WETH** (b_t) (annualized). Convert to per-step factor:
  (r^{\text{debt}}*t = \exp!\big(b_t \cdot \Delta t*{\text{yr}}\big)).
* **(Optional) weETH secondary market discount** (d_t) in bps used when SELLING weETH to unwind via DEX (put 0 if you never unwind in ETH-base case).
* **(Optional) Aave parameters over time:** LTV (t), Liquidation Threshold (LT), eMode eligibility flags. Default constant (t=0.92), (LT \approx 0.97).

## State variables

* **Collateral in weETH units** (C^{\text{weETH}}_t).
* **Debt in WETH units** (D^{\text{WETH}}_t).
* **Equity in USD** (E_t).
* **ETH price** (P_t) (from inputs).

---

# 2) Economics (no hedge, ETH-base)

This sleeve is **long ETH via weETH**, funded by **borrowing WETH** and restaking. In ETH terms:

* **Collateral growth (weETH accrual):**
  (C^{\text{weETH}}*{t+1} = C^{\text{weETH}}*{t} \cdot r^{\text{weETH}}_t)
* **Debt growth (WETH interest):**
  (D^{\text{WETH}}*{t+1} = D^{\text{WETH}}*{t} \cdot r^{\text{debt}}_t)

In **USD** at time (t):

* Collateral USD = (C^{\text{weETH}}_t \cdot P_t)
* Debt USD = (D^{\text{WETH}}_t \cdot P_t)
* **Equity** (E_t = (C^{\text{weETH}}_t - D^{\text{WETH}}_t)\cdot P_t)

**ETH price cancels** in Health Factor (HF) while you remain ETH-only (see §4), but **P&L is in ETH terms** plus accrual differentials (weETH yield – borrow APR).

---

# 3) Initial bootstrap (single shot)

Given initial equity **(E_0) USD** and target LTV (t=0.92):

1. Convert all equity to **ETH**, then stake to **weETH** (you can also model starting with ETH units directly).

   * Initial weETH units: (C^{\text{weETH}}_0 = \dfrac{E_0}{P_0})

2. **Leverage to target LTV** in one go (or iterate; results are equivalent):

   * Target **debt** at t: (D^{\text{WETH}}_0 = t \cdot C^{\text{weETH}}_0)
     (because at t, ( \text{Debt} = t \times \text{Collateral} ) in ETH units)
   * If you prefer iterative “borrow → stake → supply”:

     * Geometric series multiplier (M=\dfrac{1}{1-t}), debt multiplier (D=\dfrac{t}{1-t})
     * Final (C^{\text{weETH}}_0 = \dfrac{E_0}{P_0}\cdot M), (D^{\text{WETH}}_0 = \dfrac{E_0}{P_0}\cdot D)
   * For (t=0.92): (M=12.5), (D=11.5)

**Sanity check (ETH units):**
Net ETH long (= C_0 - D_0 = (M-D)\cdot \frac{E_0}{P_0} = \frac{E_0}{P_0}) (i.e., your initial ETH; leverage doesn’t change net ETH in this ETH-only construction).

---

# 4) Risk & constraints

## Health Factor (HF)

With **ETH-only** collateral & debt and eMode:

[
\text{HF}_t \approx \frac{LT \cdot C^{\text{weETH}}_t \cdot P_t}{D^{\text{WETH}}_t \cdot P_t}
= LT \cdot \frac{C^{\text{weETH}}_t}{D^{\text{WETH}}_t}
]

* ETH/USD cancels → **price moves don’t change HF** (to first order).
* HF **improves** slowly because weETH accrues faster (if (y>b)).
* **Liquidation event** when HF ( \le 1) → track & stop out if it happens (shouldn’t under normal params).

## weETH discount

If you **never unwind**, discount doesn’t apply. If you **simulate stress unwinds**, when selling weETH for ETH:

* Execution cost (fees+slippage) (c) (bps) and **discount** (d_t) (bps) reduce proceed ETH units:
  [
  \text{ETH out} = \text{weETH sold} \times (1 - c) \times (1 - d_t)
  ]

---

# 5) Simulation loop (per timestep)

For each step (t \to t+1):

1. **Accrue collateral & debt:**

   * (C \leftarrow C \cdot r^{\text{weETH}}_t)
   * (D \leftarrow D \cdot r^{\text{debt}}_t)

2. **(Optional) Maintain target LTV t:**

   * Compute current LTV in ETH units: ( \ell = D/C )
   * If ( \ell ) deviates beyond a band (e.g., ±50–100 bps), **rebalance**:

     * If ( \ell < t ): borrow ΔWETH = ((t - \ell)\cdot C), stake → add to (C), increase (D) by same Δ.
     * If ( \ell > t ): repay ΔWETH, reduce (D), withdraw proportionate weETH and burn to ETH as needed (apply fees/discounts if modeling unwind).

3. **Compute tracking metrics:** equity (E_t), HF, APY-to-date, drawdowns (in ETH & USD).

4. **Stops/constraints:** if HF ≤ 1 (liquidation), if borrow caps hit, or if rates exceed a max, mark a constraint breach.

---

# 6) Output metrics

* **Annualized return (ETH-base):**
  (\text{APY} \approx \frac{E_T/E_0 - 1}{\text{years}}) (you can also compute in ETH units).
* **Carry decomposition:** cumulative weETH accrual vs cumulative borrow cost.
* **HF path**, min HF, time to reach HF targets.
* **Sensitivity grids:** vary (t), (y), (b); produce heatmaps.
* **Stress tests:** weETH discount spikes (e.g., −100 bps for a week); borrow APR spikes; pausing accrual.

---

# 7) Closed-form expectation (sanity check)

If you **hold LTV exactly at t** and treat yields as constants (y) (weETH) and (b) (borrow), the **expected net APY on equity** is:

[
\text{APY}_{\text{net}} = \frac{y}{1-t} - \frac{b \cdot t}{1-t}
= \frac{y - b\cdot t}{1-t}
]

For **(t=0.92), (y=5.25%), (b=2.6%)**:

* (M=12.5), (D=11.5)
* (\text{APY} = 0.0525\times 12.5 - 0.026\times 11.5 = 0.35725 \approx \mathbf{35.73%})

Your path simulation should converge to this number (modulo drift from discrete compounding, rebalancing bands, and any unwind costs modeled).

---

# 8) Pseudocode

```python
# Params
t = 0.92                       # target LTV (ETH terms)
LT = 0.97                      # liquidation threshold (example)
dt_yr = 1/8760                 # hourly steps
y_annual = 0.0525              # weETH base (stake+Eigen+seasonal)
rebalance_band = 0.005         # +/- 50 bps around t
fee_bps = 0.0                  # set >0 only if modeling unwinds
disc_bps_ts = 0.0              # timeseries or 0

# Initial state
E0_usd = 100_000
P0 = price_ts[0]
C = (E0_usd / P0) * (1/(1-t))  # weETH units after leverage-up
D = (E0_usd / P0) * (t/(1-t))  # WETH units of debt

for t_idx in range(T-1):
    P = price_ts[t_idx]
    b_annual = borrow_apr_ts[t_idx]
    # per-step factors
    r_weeth = math.exp(y_annual * dt_yr)
    r_debt  = math.exp(b_annual * dt_yr)

    # Accrue
    C *= r_weeth
    D *= r_debt

    # Rebalance to target LTV within band
    ltv_eth = D / C
    if ltv_eth < (t - rebalance_band):
        delta = (t - ltv_eth) * C              # WETH to borrow
        D += delta
        C += delta                              # stake -> weETH
    elif ltv_eth > (t + rebalance_band):
        delta = (ltv_eth - t) * C               # WETH to repay
        # unwind: sell weETH -> ETH (optional fees/discounts)
        if fee_bps or isinstance(disc_bps_ts, float) and disc_bps_ts:
            eff = (1 - fee_bps/1e4) * (1 - disc_bps_ts/1e4)
            weeth_to_sell = delta               # repay in WETH units
            eth_out = weeth_to_sell * eff
            C -= weeth_to_sell
            D -= min(delta, eth_out)
        else:
            C -= delta
            D -= delta

    # Health factor
    HF = (LT * C * P) / (D * P)
    # Track E, HF, etc.
```

---

# 9) Calibration & validation

* **Back out y and b from history**: use realized staking/Eigen/seasonal paths (weETH index) and realized borrow APY history (Aave v3 WETH variable borrow rate).
* **No-drift test**: with constant (y,b) and no rebalancing slippage, the simulated APY should converge to the closed-form ( \frac{y - b t}{1-t} ).
* **HF monotonicity**: if (y > b), HF should **creep up** over time; if (y < b), it should **creep down**.
* **Shock tests**: insert a −100 bps weETH discount for a day; verify HF impact if you had to unwind during the discount.

---

# 10) Reporting (what to plot)

* Equity curve in **ETH** and **USD**.
* **HF** over time (min HF annotated).
* **Carry decomposition**: cumulative weETH accrual vs cumulative debt interest.
* Heatmap of net APY vs (t \in [0.7, 0.93]) and (b \in [2%,5%]).
* Scenario table: base (constant), historical (b_t), “stress” with rate spikes, “discount unwind” day.

---

## Quick numeric sanity (E₀=$100k, P₀=$2k)

* Initial ETH = 50; with (t=0.92):
  (C_0=50\times 12.5=625) ETH, (D_0=50\times 11.5=575) ETH, net = 50 ETH.
* With (y=5.25%), (b=2.6%): expected APY ≈ **35.73%** (ETH-base).
* If you remove seasonals (y=4%), APY ≈ ((0.04-0.026\times0.92)/(0.08)=20.1%).

This should give your quant everything needed to code, validate, and calibrate against your earlier high-level numbers.
