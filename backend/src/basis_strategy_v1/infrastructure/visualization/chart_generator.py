"""Chart generation for backtest results using Plotly.

Generates interactive HTML charts from EventDrivenStrategyEngine results
including equity curves, PnL attribution, component performance, and more.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate interactive charts from backtest results."""

    def __init__(self, theme: str = "plotly_white",
                 config: Optional[Dict[str, Any]] = None):
        """Initialize chart generator with theme and configuration."""
        self.theme = theme
        self.config = config or {}

        # Extract output configuration flags
        output_config = self.config.get('output', {})
        self.generate_venue_balance_chart = output_config.get(
            'generate_venue_balance_chart', True)
        self.generate_token_balance_chart = output_config.get(
            'generate_token_balance_chart', True)
        self.generate_ltv_time_series = output_config.get(
            'generate_ltv_time_series', True)
        self.generate_cumulative_return_chart = output_config.get(
            'generate_cumulative_return_chart', True)
        self.generate_strategy_allocation_chart = output_config.get(
            'generate_strategy_allocation_chart', True)
        self.generate_yield_breakdown_chart = output_config.get(
            'generate_yield_breakdown_chart', True)
        self.generate_cost_breakdown_chart = output_config.get(
            'generate_cost_breakdown_chart', True)
        self.generate_margin_time_series = output_config.get(
            'generate_margin_time_series', False)
        self.generate_eth_move_analysis = output_config.get(
            'generate_eth_move_analysis', False)
        self.save_data_csv = output_config.get('save_data_csv', True)

        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }

        logger.info(f"ChartGenerator initialized with output flags: "
                    f"venue_balance={self.generate_venue_balance_chart}, "
                    f"token_balance={self.generate_token_balance_chart}, "
                    f"ltv_series={self.generate_ltv_time_series}, "
                    f"save_csv={self.save_data_csv}")

    def generate_all_charts(
        self,
        results: Dict[str, Any],
        request_id: str,
        strategy_name: str,
        output_dir: Path
    ) -> Dict[str, Path]:
        """
        Generate all charts for a backtest result.

        Args:
            results: EventDrivenStrategyEngine results
            request_id: Backtest request ID
            strategy_name: Strategy name
            output_dir: Directory to save charts

        Returns:
            Dictionary mapping chart names to file paths
        """
        try:
            logger.info(
                f"Generating charts for {request_id} ({strategy_name})")

            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)

            chart_paths = {}

            # Generate individual charts based on configuration flags
            charts_to_generate = []

            # Always generate core charts
            charts_to_generate.append(
                ('equity_curve', self._generate_equity_curve))
            charts_to_generate.append(
                ('pnl_attribution', self._generate_pnl_attribution))

            # Optional charts based on configuration and requested UI set
            # Explicit six charts required by UI
            charts_to_generate.append(
                ('component_performance', self._generate_component_performance))
            charts_to_generate.append(
                ('fee_breakdown', self._generate_fee_breakdown))
            charts_to_generate.append(
                ('metrics_summary', self._generate_metrics_summary))

            # Implemented additional charts requested by UI
            charts_to_generate.append(('ltv_ratio', self._generate_ltv_ratio))
            charts_to_generate.append(
                ('balance_venue', self._generate_balance_venue))
            charts_to_generate.append(
                ('balance_token', self._generate_balance_token))
            charts_to_generate.append(
                ('margin_health', self._generate_margin_health))
            charts_to_generate.append(('exposure', self._generate_exposure))

            # Always generate trade history (placeholder)
            charts_to_generate.append(
                ('trade_history', self._generate_trade_history))

            # Legacy optional toggles (kept but superseded by explicit charts above)
            # Generate ETH move analysis if enabled
            if self.generate_eth_move_analysis:
                charts_to_generate.append(
                    ('eth_move_analysis', self._generate_eth_move_analysis))

            for chart_name, generator_func in charts_to_generate:
                try:
                    chart_path = output_dir / \
                        f"{request_id}_{strategy_name}_{chart_name}.html"
                    fig = generator_func(results, request_id, strategy_name)
                    if fig:
                        fig.write_html(str(chart_path))
                        chart_paths[chart_name] = chart_path
                        logger.debug(
                            f"Generated {chart_name} chart: {chart_path}")
                except Exception as e:
                    logger.warning(
                        f"Failed to generate {chart_name} chart: {e}")

            # Save data to CSV if enabled
            if self.save_data_csv:
                try:
                    self._save_data_csv(
                        results, request_id, strategy_name, output_dir)
                    logger.debug(f"Saved data CSV files for {request_id}")
                except Exception as e:
                    logger.warning(f"Failed to save CSV data: {e}")

            # Generate comprehensive dashboard
            try:
                dashboard_path = output_dir / \
                    f"{request_id}_{strategy_name}_dashboard.html"
                dashboard_fig = self._generate_dashboard(
                    results, request_id, strategy_name)
                if dashboard_fig:
                    dashboard_fig.write_html(str(dashboard_path))
                    chart_paths['dashboard'] = dashboard_path
                    logger.info(f"Generated dashboard: {dashboard_path}")
            except Exception as e:
                logger.warning(f"Failed to generate dashboard: {e}")

            logger.info(
                f"Generated {len(chart_paths)} charts for {request_id}")
            return chart_paths

        except Exception as e:
            logger.error(f"Failed to generate charts: {e}")
            return {}

    def _generate_equity_curve(self,
                               results: Dict[str,
                                             Any],
                               request_id: str,
                               strategy_name: str) -> Optional[go.Figure]:
        """Generate equity curve chart using real time series data."""
        try:
            # Extract real equity curve data from results
            equity_curve = results.get('equity_curve', [])
            initial_capital = results.get('initial_capital', 0)
            final_value = results.get('final_value', 0)
            gross_value = results.get('gross_value', final_value)
            total_fees_paid = results.get('total_fees_paid', 0)

            # DEBUG: Log what data we received
            logger.info(f"Chart generation debug for {request_id}:")
            if equity_curve is None:
                logger.warning("  Equity curve data is None - will use fallback", extra={"error_code": "CHART_ERROR_001"})
            elif not equity_curve:
                logger.warning("  No equity curve data - will use fallback", extra={"error_code": "CHART_ERROR_002"})
            else:
                logger.info(f"  Equity curve data points: {len(equity_curve)}")
                logger.info(f"  First point: {equity_curve[0]}")
                logger.info(f"  Last point: {equity_curve[-1]}")

            if not equity_curve or equity_curve is None:
                logger.warning(
                    "No equity curve data available, creating placeholder", extra={"error_code": "CHART_ERROR_003"})
                # Fallback to simple curve if no time series data
                dates = [datetime.now() - timedelta(days=1), datetime.now()]
                net_values = [initial_capital, final_value]
                gross_values = [initial_capital, gross_value]
            else:
                # Use real time series data
                dates = [point['timestamp'] for point in equity_curve]
                net_values = [point['net_value'] for point in equity_curve]
                gross_values = [point['gross_value'] for point in equity_curve]

            fig = go.Figure()

            # Add net portfolio value (after fees)
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=net_values,
                    mode='lines',
                    name='Net Portfolio Value',
                    line=dict(
                        color=self.colors['primary'],
                        width=3),
                    hovertemplate='<b>%{x}</b><br>Net Value: $%{y:,.2f}<extra></extra>'))

            # Add gross portfolio value (before fees)
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=gross_values,
                    mode='lines',
                    name='Gross Portfolio Value',
                    line=dict(
                        color=self.colors['info'],
                        width=2,
                        dash='dot'),
                    hovertemplate='<b>%{x}</b><br>Gross Value: $%{y:,.2f}<extra></extra>'))

            # Add benchmark line (initial capital)
            fig.add_hline(
                y=initial_capital,
                line_dash="dash",
                line_color=self.colors['secondary'],
                annotation_text="Initial Capital"
            )

            # Add fee impact annotation
            if total_fees_paid > 0:
                fig.add_annotation(
                    x=dates[-1] if dates else datetime.now(),
                    y=final_value,
                    text=f"Total Fees: ${total_fees_paid:,.2f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor=self.colors['danger'],
                    bgcolor=self.colors['light'],
                    bordercolor=self.colors['danger']
                )

            fig.update_layout(
                title=f'Equity Curve - {strategy_name}<br><sub>Net: ${final_value:,.2f} | Gross: ${gross_value:,.2f} | Fees: ${total_fees_paid:,.2f}</sub>',
                xaxis_title='Date',
                yaxis_title='Portfolio Value ($)',
                template=self.theme,
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01))

            return fig

        except Exception as e:
            logger.error(f"Error generating equity curve: {e}")
            return None

    def _token_parent(self, token: str) -> str:
        """Map derivative/wrapped tokens to parent token for exposure aggregation."""
        if not token:
            return "UNKNOWN"
        t = token.upper()
        if t in ["USDT"]:
            return "USD"
        if t in ["ETH", "WETH", "STETH", "WSTETH", "EETH", "WEETH"]:
            return "ETH"
        return t

    def _price_for_token(self, token: str, timestamp) -> float:
        """Return a best-effort USD price for token at timestamp using config defaults.
        Stablecoins = 1.0; ETH family uses backtest.default_eth_price; else 0 (ignored).
        """
        parent = self._token_parent(token)
        if parent == "USD":
            return 1.0
        if parent == "ETH":
            try:
                return float(
                    self.config.get(
                        'backtest',
                        {}).get(
                        'default_eth_price',
                        3000.0))
            except Exception:
                return 3000.0
        return 0.0

    def _snapshot_positions(
            self, snapshot: Dict[str, Any]) -> Dict[str, float]:
        """Get positions dict from an equity_curve snapshot (safe)."""
        positions = snapshot.get('positions') or {}
        # Ensure plain dict of floats
        safe: Dict[str, float] = {}
        for k, v in positions.items():
            try:
                safe[str(k)] = float(v)
            except Exception:
                continue
        return safe

    def _generate_exposure(self,
                           results: Dict[str,
                                         Any],
                           request_id: str,
                           strategy_name: str) -> Optional[go.Figure]:
        """Generate net exposure by parent token, accounting for futures (perps) and token equity.

        Net exposure per parent token = (assets_usd - debts_usd) - perps_usd
        where perps_usd reduces exposure (assumes positive value represents short hedge typical in basis).
        """
        try:
            equity_curve = results.get('equity_curve', [])
            if not equity_curve:
                return None
            # Build time series
            timestamps: List = []
            exposures_by_token: Dict[str, List[float]] = {}
            for snap in equity_curve:
                ts = snap.get('timestamp')
                timestamps.append(ts)
                positions = self._snapshot_positions(snap)
                # Aggregate assets, debts, perps per token parent
                assets_usd: Dict[str, float] = {}
                debts_usd: Dict[str, float] = {}
                perps_usd: Dict[str, float] = {}
                for key, amount in positions.items():
                    parts = key.split('_')
                    if not parts:
                        continue
                    token = parts[0]
                    parent = self._token_parent(token)
                    price = self._price_for_token(token, ts)
                    if price == 0.0:
                        continue
                    is_debt = 'DEBT' in key
                    is_perp = key.endswith('_PERP') or ('_PERP_' in key)
                    usd_val = amount * price
                    if is_perp:
                        perps_usd[parent] = perps_usd.get(
                            parent, 0.0) + abs(usd_val)
                    elif is_debt:
                        debts_usd[parent] = debts_usd.get(
                            parent, 0.0) + abs(usd_val)
                    else:
                        assets_usd[parent] = assets_usd.get(
                            parent, 0.0) + usd_val
                # Compute net exposure per parent
                parents = set(
                    list(
                        assets_usd.keys()) +
                    list(
                        debts_usd.keys()) +
                    list(
                        perps_usd.keys()))
                for parent in parents:
                    net = assets_usd.get(parent,
                                         0.0) - debts_usd.get(parent,
                                                              0.0) - perps_usd.get(parent,
                                                                                   0.0)
                    if parent not in exposures_by_token:
                        exposures_by_token[parent] = []
                    exposures_by_token[parent].append(net)
                # Ensure same length across tokens by padding zeros for missing
                for parent in exposures_by_token.keys():
                    if len(exposures_by_token[parent]) < len(timestamps):
                        exposures_by_token[parent].append(0.0)

            if not exposures_by_token:
                return None

            fig = go.Figure()
            for parent, values in exposures_by_token.items():
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=values,
                    mode='lines',
                    name=f"{parent} Exposure",
                ))
            fig.update_layout(
                title=f"Net Exposure by Token - {strategy_name}",
                xaxis_title='Date',
                yaxis_title='Exposure (USD)',
                template=self.theme,
                hovermode='x unified'
            )
            return fig
        except Exception as e:
            logger.error(f"Error generating exposure chart: {e}")
            return None

    def _generate_balance_token(self,
                                results: Dict[str,
                                              Any],
                                request_id: str,
                                strategy_name: str) -> Optional[go.Figure]:
        """Generate aggregated token balances (assets - debt) over time in USD."""
        try:
            equity_curve = results.get('equity_curve', [])
            if not equity_curve:
                return None
            timestamps: List = []
            balances_by_token: Dict[str, List[float]] = {}
            for snap in equity_curve:
                ts = snap.get('timestamp')
                timestamps.append(ts)
                positions = self._snapshot_positions(snap)
                assets_usd: Dict[str, float] = {}
                debts_usd: Dict[str, float] = {}
                for key, amount in positions.items():
                    token = key.split('_')[0]
                    parent = self._token_parent(token)
                    price = self._price_for_token(token, ts)
                    if price == 0.0:
                        continue
                    usd_val = amount * price
                    if 'DEBT' in key:
                        debts_usd[parent] = debts_usd.get(
                            parent, 0.0) + abs(usd_val)
                    elif key.endswith('_PERP') or ('_PERP_' in key):
                        # Ignore perps in balance_token (exposure is separate)
                        continue
                    else:
                        assets_usd[parent] = assets_usd.get(
                            parent, 0.0) + usd_val
                parents = set(list(assets_usd.keys()) + list(debts_usd.keys()))
                for parent in parents:
                    net = assets_usd.get(parent, 0.0) - \
                        debts_usd.get(parent, 0.0)
                    if parent not in balances_by_token:
                        balances_by_token[parent] = []
                    balances_by_token[parent].append(net)
                for parent in balances_by_token.keys():
                    if len(balances_by_token[parent]) < len(timestamps):
                        balances_by_token[parent].append(0.0)
            if not balances_by_token:
                return None
            fig = go.Figure()
            for parent, values in balances_by_token.items():
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=values,
                        mode='lines',
                        name=parent))
            fig.update_layout(
                title=f"Token Balances (Net) - {strategy_name}",
                xaxis_title='Date',
                yaxis_title='Balance (USD)',
                template=self.theme,
                hovermode='x unified'
            )
            return fig
        except Exception as e:
            logger.error(f"Error generating token balance chart: {e}")
            return None

    def _generate_balance_venue(self,
                                results: Dict[str,
                                              Any],
                                request_id: str,
                                strategy_name: str) -> Optional[go.Figure]:
        """Generate balances by venue over time in USD (assets only)."""
        try:
            equity_curve = results.get('equity_curve', [])
            if not equity_curve:
                return None
            timestamps: List = []
            balances_by_venue: Dict[str, List[float]] = {}
            for snap in equity_curve:
                ts = snap.get('timestamp')
                timestamps.append(ts)
                positions = self._snapshot_positions(snap)
                venue_totals: Dict[str, float] = {}
                for key, amount in positions.items():
                    parts = key.split('_')
                    if len(parts) < 2:
                        continue
                    token, venue = parts[0], parts[1]
                    if 'DEBT' in key or key.endswith(
                            '_PERP') or '_PERP_' in key:
                        continue
                    price = self._price_for_token(token, ts)
                    if price == 0.0:
                        continue
                    usd_val = amount * price
                    venue_totals[venue] = venue_totals.get(
                        venue, 0.0) + usd_val
                for venue, total in venue_totals.items():
                    if venue not in balances_by_venue:
                        balances_by_venue[venue] = []
                    balances_by_venue[venue].append(total)
                for venue in balances_by_venue.keys():
                    if len(balances_by_venue[venue]) < len(timestamps):
                        balances_by_venue[venue].append(0.0)
            if not balances_by_venue:
                return None
            fig = go.Figure()
            for venue, values in balances_by_venue.items():
                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=values,
                        mode='lines',
                        name=venue))
            fig.update_layout(
                title=f"Balances by Venue - {strategy_name}",
                xaxis_title='Date',
                yaxis_title='Balance (USD)',
                template=self.theme,
                hovermode='x unified'
            )
            return fig
        except Exception as e:
            logger.error(f"Error generating venue balance chart: {e}")
            return None

    def _generate_ltv_ratio(self,
                            results: Dict[str,
                                          Any],
                            request_id: str,
                            strategy_name: str) -> Optional[go.Figure]:
        """Generate LTV ratio over time using AAVE balances and debts."""
        try:
            equity_curve = results.get('equity_curve', [])
            if not equity_curve:
                return None
            timestamps: List = []
            ltv_values: List[float] = []
            for snap in equity_curve:
                ts = snap.get('timestamp')
                timestamps.append(ts)
                positions = self._snapshot_positions(snap)
                collateral_usd = 0.0
                debt_usd = 0.0
                for key, amount in positions.items():
                    token = key.split('_')[0]
                    price = self._price_for_token(token, ts)
                    if price == 0.0:
                        continue
                    if '_AAVE' in key and 'DEBT' not in key:
                        collateral_usd += amount * price
                    if 'DEBT' in key:
                        debt_usd += abs(amount) * price
                ltv = (debt_usd / collateral_usd) if collateral_usd > 0 else 0.0
                ltv_values.append(ltv)
            fig = go.Figure(
                go.Scatter(
                    x=timestamps,
                    y=ltv_values,
                    mode='lines',
                    name='LTV'))
            fig.update_layout(
                title=f"AAVE LTV Ratio - {strategy_name}",
                xaxis_title='Date',
                yaxis_title='LTV',
                template=self.theme,
                hovermode='x unified',
                yaxis=dict(range=[0, max(1.0, max(ltv_values) if ltv_values else 1.0)])
            )
            return fig
        except Exception as e:
            logger.error(f"Error generating LTV ratio chart: {e}")
            return None

    def _generate_margin_health(self,
                                results: Dict[str,
                                              Any],
                                request_id: str,
                                strategy_name: str) -> Optional[go.Figure]:
        """Generate simple margin health proxy for futures positions.

        Approximation:
        - perps_usd = sum(|perp size| * price)
        - used_margin = perps_usd * 0.10 (assumes 10% initial margin)
        - current_margin = USD balances (stablecoins) across venues
        - margin_ratio = (current_margin + used_margin) / perps_usd (0 if no perps)
        """
        try:
            equity_curve = results.get('equity_curve', [])
            if not equity_curve:
                return None
            timestamps: List = []
            health_values: List[float] = []
            for snap in equity_curve:
                ts = snap.get('timestamp')
                timestamps.append(ts)
                positions = self._snapshot_positions(snap)
                perps_usd = 0.0
                usd_balances = 0.0
                for key, amount in positions.items():
                    token = key.split('_')[0]
                    parent = self._token_parent(token)
                    if key.endswith('_PERP') or ('_PERP_' in key):
                        price = self._price_for_token(token, ts)
                        perps_usd += abs(amount) * price
                    elif parent == 'USD' and 'DEBT' not in key:
                        # Count all stablecoin balances as margin
                        usd_balances += float(amount)
                used_margin = perps_usd * 0.10
                health = ((usd_balances + used_margin) /
                          perps_usd) if perps_usd > 0 else 0.0
                health_values.append(health)
            fig = go.Figure(
                go.Scatter(
                    x=timestamps,
                    y=health_values,
                    mode='lines',
                    name='Margin Health'))
            fig.update_layout(
                title=f"Margin Health (Proxy) - {strategy_name}",
                xaxis_title='Date',
                yaxis_title='Health Ratio',
                template=self.theme,
                hovermode='x unified'
            )
            return fig
        except Exception as e:
            logger.error(f"Error generating margin health chart: {e}")
            return None

    def _generate_pnl_attribution(self,
                                  results: Dict[str,
                                                Any],
                                  request_id: str,
                                  strategy_name: str) -> Optional[go.Figure]:
        """Generate PnL attribution chart."""
        try:
            component_summaries = results.get('component_summaries', {})

            # Extract PnL from each component
            pnl_data = {}

            if 'lending' in component_summaries:
                lending_summary = component_summaries['lending']
                pnl_data['Lending Interest'] = lending_summary.get(
                    'total_interest_usd', 0)
                pnl_data['Lending Fees'] = - \
                    lending_summary.get('gas_costs_paid', 0)

            if 'staking' in component_summaries:
                staking_summary = component_summaries['staking']
                pnl_data['Staking Yield'] = staking_summary.get(
                    'total_yield_usd', 0)
                pnl_data['Staking Fees'] = - \
                    staking_summary.get('gas_costs_paid', 0)

            if 'basis_trading' in component_summaries:
                basis_summary = component_summaries['basis_trading']
                pnl_data['Funding Payments'] = basis_summary.get(
                    'total_funding_usd', 0)
                pnl_data['Trading Fees'] = - \
                    basis_summary.get('total_fees_usd', 0)

            if not pnl_data:
                # Fallback to simple total return
                total_return = results.get('total_return', 0)
                initial_capital = results.get('initial_capital', 1)
                pnl_data['Total PnL'] = float(
                    total_return) * float(initial_capital)

            # Create waterfall chart
            categories = list(pnl_data.keys())
            values = list(pnl_data.values())

            fig = go.Figure(go.Waterfall(
                name="PnL Attribution",
                orientation="v",
                measure=["relative"] * len(categories),
                x=categories,
                textposition="outside",
                text=[f"${v:+,.2f}" for v in values],
                y=values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": self.colors['success']}},
                decreasing={"marker": {"color": self.colors['danger']}},
                totals={"marker": {"color": self.colors['info']}}
            ))

            fig.update_layout(
                title=f'PnL Attribution - {strategy_name}',
                xaxis_title='Component',
                yaxis_title='PnL ($)',
                template=self.theme
            )

            return fig

        except Exception as e:
            logger.error(f"Error generating PnL attribution: {e}")
            return None

    def _generate_component_performance(self,
                                        results: Dict[str,
                                                      Any],
                                        request_id: str,
                                        strategy_name: str) -> Optional[go.Figure]:
        """Generate component performance comparison."""
        try:
            component_summaries = results.get('component_summaries', {})
            components_used = results.get('components_used', [])

            if not component_summaries:
                return None

            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Returns by Component', 'Fees by Component',
                                'Volume by Component', 'Efficiency Ratio'),
                specs=[[{"type": "bar"}, {"type": "bar"}],
                       [{"type": "bar"}, {"type": "scatter"}]]
            )

            components = []
            returns = []
            fees = []
            volumes = []

            for component_name, summary in component_summaries.items():
                components.append(component_name.title())

                # Extract returns
                if 'total_interest_usd' in summary:
                    returns.append(summary['total_interest_usd'])
                elif 'total_yield_usd' in summary:
                    returns.append(summary['total_yield_usd'])
                elif 'net_profit' in summary:
                    returns.append(summary['net_profit'])
                else:
                    returns.append(0)

                # Extract fees
                fees.append(
                    summary.get(
                        'gas_costs_paid',
                        0) +
                    summary.get(
                        'total_fees_usd',
                        0))

                # Extract volumes
                volumes.append(
                    summary.get(
                        'total_supplied_usd',
                        0) +
                    summary.get(
                        'total_staked_usd',
                        0))

            # Returns by component
            fig.add_trace(
                go.Bar(
                    x=components,
                    y=returns,
                    name='Returns',
                    marker_color=self.colors['success']),
                row=1,
                col=1)

            # Fees by component
            fig.add_trace(
                go.Bar(
                    x=components,
                    y=fees,
                    name='Fees',
                    marker_color=self.colors['danger']),
                row=1,
                col=2)

            # Volume by component
            fig.add_trace(
                go.Bar(
                    x=components,
                    y=volumes,
                    name='Volume',
                    marker_color=self.colors['info']),
                row=2,
                col=1)

            # Efficiency ratio (returns/fees)
            efficiency = [r / f if f > 0 else 0 for r, f in zip(returns, fees)]
            fig.add_trace(
                go.Scatter(
                    x=components,
                    y=efficiency,
                    mode='markers+lines',
                    name='Efficiency',
                    marker_color=self.colors['primary']),
                row=2,
                col=2)

            fig.update_layout(
                title=f'Component Performance - {strategy_name}',
                template=self.theme,
                showlegend=False
            )

            return fig

        except Exception as e:
            logger.error(f"Error generating component performance: {e}")
            return None

    def _generate_balance_evolution(self,
                                    results: Dict[str,
                                                  Any],
                                    request_id: str,
                                    strategy_name: str) -> Optional[go.Figure]:
        """Generate balance evolution over time."""
        # Placeholder - would need time series data from
        # EventDrivenStrategyEngine
        return None

    def _generate_rates_yields(self,
                               results: Dict[str,
                                             Any],
                               request_id: str,
                               strategy_name: str) -> Optional[go.Figure]:
        """Generate rates and yields chart."""
        # Placeholder - would show lending rates, staking yields over time
        return None

    def _generate_fee_breakdown(self,
                                results: Dict[str,
                                              Any],
                                request_id: str,
                                strategy_name: str) -> Optional[go.Figure]:
        """Generate fee breakdown pie chart."""
        try:
            component_summaries = results.get('component_summaries', {})

            fee_data = {}
            for component_name, summary in component_summaries.items():
                gas_fees = summary.get('gas_costs_paid', 0)
                other_fees = summary.get('total_fees_usd', 0)

                if gas_fees > 0:
                    fee_data[f'{component_name.title()} Gas'] = gas_fees
                if other_fees > 0:
                    fee_data[f'{component_name.title()} Fees'] = other_fees

            if not fee_data:
                return None

            fig = go.Figure(data=[go.Pie(
                labels=list(fee_data.keys()),
                values=list(fee_data.values()),
                hole=0.3,
                textinfo='label+percent',
                textposition='auto'
            )])

            fig.update_layout(
                title=f'Fee Breakdown - {strategy_name}',
                template=self.theme
            )

            return fig

        except Exception as e:
            logger.error(f"Error generating fee breakdown: {e}")
            return None

    def _generate_trade_history(self,
                                results: Dict[str,
                                              Any],
                                request_id: str,
                                strategy_name: str) -> Optional[go.Figure]:
        """Generate trade history timeline."""
        # Placeholder - would show trade execution timeline
        return None

    def _generate_metrics_summary(self,
                                  results: Dict[str,
                                                Any],
                                  request_id: str,
                                  strategy_name: str) -> Optional[go.Figure]:
        """Generate metrics summary dashboard."""
        try:
            # Compute additional metrics
            initial_capital = float(results.get('initial_capital', 0) or 0)
            final_value = float(results.get('final_value', 0) or 0)
            total_return = float(results.get('total_return', 0) or 0)
            sharpe_ratio = float(results.get('sharpe_ratio', 0) or 0)
            max_drawdown = float(results.get('max_drawdown', 0) or 0)

            # Days in period
            import datetime as _dt
            start = results.get('start_date')
            end = results.get('end_date')

            def _to_dt(v):
                if v is None:
                    return None
                if isinstance(v, _dt.datetime):
                    return v
                try:
                    return _dt.datetime.fromisoformat(
                        str(v).replace('Z', '+00:00'))
                except Exception:
                    return None
            dt0 = _to_dt(start)
            dt1 = _to_dt(end)
            days = None
            if dt0 and dt1:
                days = max(1, int((dt1 - dt0).total_seconds() // 86400))

            # Estimate traded notional and ADV from equity snapshots
            total_traded_usd = self._estimate_total_traded_volume(results)
            adv_usd = (total_traded_usd / days) if (days and days > 0) else 0.0
            pnl_usd = max(
                0.0,
                final_value -
                initial_capital) if (
                initial_capital and final_value) else (
                total_return *
                initial_capital)
            pnl_bps = ((pnl_usd / total_traded_usd) *
                       10000.0) if total_traded_usd > 0 else 0.0

            # Key metrics (formatted)
            metrics = {
                'Total Return': f"{total_return:.2%}",
                'Annualized Return (APR)': f"{float(results.get('annualized_return', 0)):.2%}",
                'Sharpe Ratio': f"{sharpe_ratio:.2f}",
                'Max Drawdown': f"{max_drawdown:.2%}",
                'Initial Capital': f"${initial_capital:,.2f}",
                'Final Value': f"${final_value:,.2f}",
                'Total Trades': results.get(
                    'total_trades',
                    0),
                'Notional Traded (USD)': f"${total_traded_usd:,.0f}",
                'Average Daily Volume (USD)': f"${adv_usd:,.0f}",
                'PnL (bps)': f"{pnl_bps:.1f}",
                'Architecture': results.get(
                    'architecture',
                    'Unknown'),
                'Components Used': len(
                    results.get(
                        'components_used',
                        []))}

            # Create a simple table-like visualization
            fig = go.Figure()

            # Add text annotations for metrics
            y_positions = list(range(len(metrics)))[
                ::-1]  # Reverse for top-to-bottom

            for i, (metric, value) in enumerate(metrics.items()):
                fig.add_annotation(
                    x=0, y=y_positions[i],
                    text=f"<b>{metric}:</b> {value}",
                    showarrow=False,
                    font=dict(size=14),
                    xanchor='left'
                )

            fig.update_layout(
                title=f'Metrics Summary - {strategy_name}',
                xaxis=dict(visible=False, range=[-0.1, 1]),
                yaxis=dict(visible=False, range=[-0.5, len(metrics) - 0.5]),
                template=self.theme,
                height=400
            )

            return fig

        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return None

    def _estimate_total_traded_volume(self, results: Dict[str, Any]) -> float:
        """Best-effort estimate of total traded notional in USD using equity snapshots.

        Sums absolute token unit deltas between consecutive snapshots (assets only, excludes DEBT/PERP)
        multiplied by token price.
        """
        try:
            equity_curve = results.get('equity_curve', [])
            if not equity_curve or len(equity_curve) < 2:
                # Fallback: try component_summaries volumes
                comp = results.get('component_summaries', {}) or {}
                total = 0.0
                for _, summary in comp.items():
                    for key in [
                        'total_supplied_usd',
                        'total_staked_usd',
                        'total_borrowed_usd',
                            'total_traded_usd']:
                        try:
                            total += float(summary.get(key, 0) or 0)
                        except Exception:
                            pass
                return float(total)
            total_volume = 0.0
            # Build aggregated token balances per snapshot

            def agg_tokens(snapshot):
                positions = self._snapshot_positions(snapshot)
                agg: Dict[str, float] = {}
                for key, amount in positions.items():
                    # Skip debts and perps for notional traded
                    if 'DEBT' in key or key.endswith(
                            '_PERP') or ('_PERP_' in key):
                        continue
                    token = key.split('_')[0]
                    agg[token] = agg.get(token, 0.0) + float(amount)
                return agg
            prev = agg_tokens(equity_curve[0])
            for i in range(1, len(equity_curve)):
                curr_snap = equity_curve[i]
                curr = agg_tokens(curr_snap)
                ts = curr_snap.get('timestamp')
                tokens = set(list(prev.keys()) + list(curr.keys()))
                for token in tokens:
                    prev_amt = prev.get(token, 0.0)
                    curr_amt = curr.get(token, 0.0)
                    delta = abs(curr_amt - prev_amt)
                    if delta <= 0:
                        continue
                    price = self._price_for_token(token, ts)
                    if price <= 0:
                        continue
                    total_volume += delta * price
                prev = curr
            return float(total_volume)
        except Exception as e:
            logger.warning(f"Failed to estimate traded volume: {e}")
            return 0.0

    def _generate_dashboard(self,
                            results: Dict[str,
                                          Any],
                            request_id: str,
                            strategy_name: str) -> Optional[go.Figure]:
        """Generate comprehensive dashboard with multiple charts."""
        try:
            # Create subplots for dashboard
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'Portfolio Performance', 'PnL Attribution',
                    'Component Returns', 'Fee Breakdown',
                    'Key Metrics', 'Risk Metrics'
                ),
                specs=[
                    [{"type": "scatter"}, {"type": "bar"}],
                    [{"type": "bar"}, {"type": "pie"}],
                    [{"colspan": 2}, None]
                ],
                vertical_spacing=0.08
            )

            # Add equity curve using real daily data
            equity_curve = results.get('equity_curve', [])
            initial_capital = results.get('initial_capital', 0)
            final_value = results.get('final_value', 0)

            if equity_curve:
                # Use real daily equity curve data
                dates = [point['timestamp'] for point in equity_curve]
                equity_values = [point['net_value'] for point in equity_curve]
            else:
                # Fallback to simple 2-point curve if no daily data
                dates = [datetime.now() - timedelta(days=1), datetime.now()]
                equity_values = [initial_capital, final_value]

            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=equity_values,
                    mode='lines',
                    name='Portfolio Value'),
                row=1,
                col=1)

            # Add PnL attribution
            component_summaries = results.get('component_summaries', {})
            if component_summaries:
                components = list(component_summaries.keys())
                pnl_values = [summary.get('net_profit', 0)
                              for summary in component_summaries.values()]

                fig.add_trace(
                    go.Bar(x=components, y=pnl_values, name='PnL'),
                    row=1, col=2
                )

            # Add component returns
            if component_summaries:
                returns = [
                    summary.get(
                        'total_interest_usd',
                        summary.get(
                            'total_yield_usd',
                            0)) for summary in component_summaries.values()]

                fig.add_trace(
                    go.Bar(x=components, y=returns, name='Returns'),
                    row=2, col=1
                )

            # Add fee breakdown
            fee_data = {}
            for comp_name, summary in component_summaries.items():
                fees = summary.get('gas_costs_paid', 0)
                if fees > 0:
                    fee_data[comp_name] = fees

            if fee_data:
                fig.add_trace(
                    go.Pie(
                        labels=list(
                            fee_data.keys()), values=list(
                            fee_data.values()), name='Fees'), row=2, col=2)

            fig.update_layout(
                title=f'Strategy Dashboard - {strategy_name}',
                template=self.theme,
                height=800,
                showlegend=False
            )

            return fig

        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return None

    def _generate_ltv_time_series(
            self, results: Dict[str, Any], request_id: str, strategy_name: str):
        """Generate LTV time series chart (placeholder)."""
        logger.info("LTV time series chart generation not yet implemented")
        return None

    def _generate_margin_analysis(
            self, results: Dict[str, Any], request_id: str, strategy_name: str):
        """Generate margin analysis chart (placeholder)."""
        logger.info("Margin analysis chart generation not yet implemented")
        return None

    def _generate_eth_move_analysis(
            self, results: Dict[str, Any], request_id: str, strategy_name: str):
        """Generate ETH move analysis chart (placeholder)."""
        logger.info("ETH move analysis chart generation not yet implemented")
        return None

    def _save_data_csv(self,
                       results: Dict[str,
                                     Any],
                       request_id: str,
                       strategy_name: str,
                       output_dir: Path):
        """Save backtest data to CSV files."""
        try:
            # Save equity curve data
            equity_curve = results.get('equity_curve', [])
            if equity_curve:
                df_equity = pd.DataFrame(equity_curve)
                csv_path = output_dir / \
                    f"{request_id}_{strategy_name}_equity_curve.csv"
                df_equity.to_csv(csv_path, index=False)
                logger.debug(f"Saved equity curve CSV: {csv_path}")

            # Save component summaries
            component_summaries = results.get('component_summaries', {})
            if component_summaries:
                df_components = pd.DataFrame.from_dict(
                    component_summaries, orient='index')
                csv_path = output_dir / \
                    f"{request_id}_{strategy_name}_component_summaries.csv"
                df_components.to_csv(csv_path)
                logger.debug(f"Saved component summaries CSV: {csv_path}")

            # Save trade history if available (support both keys)
            trades = results.get(
                'trades', []) or results.get(
                'trade_history', [])
            if trades:
                # Convert trades to DataFrame
                trade_data = []
                for trade in trades:
                    if hasattr(trade, '__dict__'):
                        trade_data.append(trade.__dict__)
                    else:
                        trade_data.append(trade)

                df_trades = pd.DataFrame(trade_data)
                csv_path = output_dir / \
                    f"{request_id}_{strategy_name}_trades.csv"
                df_trades.to_csv(csv_path, index=False)
                logger.debug(f"Saved trades CSV: {csv_path}")

            # Save rich event log if present
            event_log = results.get('event_log', [])
            if event_log:
                # Flatten nested dicts (positions, pnl_attribution) into
                # columns
                def flatten_entry(e: Dict[str, Any]) -> Dict[str, Any]:
                    flat = {
                        'timestamp': e.get('timestamp'),
                        'event_type': e.get('event_type'),
                        'gross_value': e.get('gross_value'),
                        'net_value': e.get('net_value'),
                        'total_fees_paid': e.get('total_fees_paid'),
                    }
                    pnl = e.get('pnl_attribution') or {}
                    for k, v in pnl.items():
                        flat[f"pnl_{k}"] = v
                    # positions as semicolon-joined k=v for CSV simplicity
                    positions = e.get('positions') or {}
                    flat['positions'] = ";".join(
                        [f"{k}={v}" for k, v in positions.items()])
                    # event_data summarized
                    event_data = e.get('event_data')
                    flat['event_data'] = str(
                        event_data) if event_data is not None else None
                    return flat
                rows = [flatten_entry(e) for e in event_log]
                df_events = pd.DataFrame(rows)
                csv_path = output_dir / \
                    f"{request_id}_{strategy_name}_event_log.csv"
                df_events.to_csv(csv_path, index=False)
                logger.debug(f"Saved event log CSV: {csv_path}")

        except Exception as e:
            logger.error(f"Error saving CSV data: {e}")
            raise
