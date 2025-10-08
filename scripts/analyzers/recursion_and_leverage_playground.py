import argparse


def calculate_recursive_leverage(ltv_initial: float, ltv_recursive: float, iterations: int, liquidation_threshold: float):
    """
    Calculate the sum of a finite geometric series for a recursive leverage strategy and the last term.
    Sum = a * (1 - r^n) / (1 - r) if r != 1 else a * n
    Last term = a * r^(n-1)
    Returns (series_sum, last_term, withdrawable_capital, liquidation_move)
    """
    if iterations <= 0:
        return 0.0, 0.0, 0.0, 0.0
    if ltv_recursive == 1.0:
        series_sum = ltv_initial * iterations
    else:
        series_sum = ltv_initial * (1 - ltv_recursive ** iterations) / (1 - ltv_recursive)
    last_term = ltv_initial * (ltv_recursive ** (iterations - 1))
    
    # Calculate withdrawable capital at the last loop
    # If last_term < ltv_recursive, we can withdraw the difference
    if last_term < ltv_recursive:
        withdrawable_capital = ltv_recursive - last_term
    else:
        withdrawable_capital = 0.0
    
    # Calculate the move against us that would trigger liquidation
    # Liquidation occurs when: collateral_value * liquidation_threshold <= debt_value
    # For a move against us: new_collateral_value = collateral_value * (1 - move)
    # Liquidation condition: collateral_value * (1 - move) * liquidation_threshold <= debt_value
    # Solving for move: move >= 1 - (debt_value / (collateral_value * liquidation_threshold))
    # Since debt_value = collateral_value * ltv_recursive:
    # move >= 1 - (ltv_recursive / liquidation_threshold)
    
    if liquidation_threshold > 0:
        liquidation_move = 1 - (ltv_recursive / liquidation_threshold)
    else:
        liquidation_move = 0.0
    
    return series_sum, last_term, withdrawable_capital, liquidation_move


def main():
    parser = argparse.ArgumentParser(description="Calculate leverage factor for a recursive yield strategy.")
    parser.add_argument("--ltv-initial", "-a", type=float, required=True, help="Initial LTV (a).")
    parser.add_argument("--ltv-recursive", "-r", type=float, required=True, help="Recursive LTV (r).")
    parser.add_argument("--iterations", "-n", type=int, default=10, help="Number of iterations (n).")
    parser.add_argument("--liquidation-threshold", "-lt", type=float, default=0.95, help="Liquidation threshold (default: 0.95 for eMode).")
    args = parser.parse_args()

    series_sum, last_term, withdrawable_capital, liquidation_move = calculate_recursive_leverage(
        args.ltv_initial, args.ltv_recursive, args.iterations, args.liquidation_threshold
    )

    print(f"Series sum (leverage factor): {series_sum:.6f}")
    print(f"Last term (final loop LTV): {last_term:.6f}")
    print(f"Withdrawable capital at last loop: {withdrawable_capital:.6f}")
    print(f"Liquidation threshold: {args.liquidation_threshold:.1%}")
    print(f"Move against us to trigger liquidation: {liquidation_move:.1%}")
    
    # Calculate actual dollar amounts for $1 initial capital
    print(f"\nFor $1 initial capital:")
    print(f"Total leveraged position: ${series_sum:.2f}")
    print(f"Final loop LTV: {last_term:.1%}")
    print(f"Withdrawable capital: ${withdrawable_capital:.2f}")
    print(f"Net capital deployed: ${series_sum - withdrawable_capital:.2f}")
    
    # Risk analysis
    print(f"\nRisk Analysis:")
    print(f"Liquidation threshold: {args.liquidation_threshold:.1%}")
    print(f"Current LTV: {args.ltv_recursive:.1%}")
    print(f"Safety buffer: {args.liquidation_threshold - args.ltv_recursive:.1%}")
    print(f"Collateral can drop by {liquidation_move:.1%} before liquidation")
    
    if liquidation_move > 0:
        print(f"✅ Safe: Collateral can drop {liquidation_move:.1%} before liquidation risk")
    else:
        print(f"⚠️  WARNING: Already at liquidation risk!")


if __name__ == "__main__":
    main()
