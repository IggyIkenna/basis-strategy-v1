# Frontend Specification - Wizard/Stepper UI 🎨

**Component**: Frontend Web Application  
**Responsibility**: User interface for strategy configuration and results viewing  
**Priority**: ⭐⭐ HIGH  
**Technology**: React + TypeScript + Tailwind CSS + shadcn/ui  
**Location**: `frontend/src/`  
**Status**: 🔧 **PARTIALLY IMPLEMENTED** - Wizard components complete, results components missing

---

## 🎯 **Purpose**

Provide intuitive wizard-based UI for:
- Strategy mode selection
- Configuration (mode-specific parameters)
- Backtest execution
- Results viewing (metrics, charts, events)
- Data download (CSV, HTML, events)

**Key Principles**:
- **Wizard/stepper flow**: Guide users through configuration
- **Mode-aware forms**: Show only relevant parameters
- **Real-time validation**: Validate as user types
- **Estimated APY**: Show expected return range
- **Embedded Plotly**: Backend-generated interactive charts
- **Responsive**: Desktop + mobile
- **Minimal**: Simple, focused, easy to use

---

## 📊 **User Flow**

### **Wizard Steps**

**Step 0: Strategy Mode Selection with Performance Guidance**
```tsx
// Display expected performance for each mode
const modePerformance = {
  'pure_lending': { target_apy: 0.05, max_drawdown: 0.005, description: 'Low risk, stable returns' },
  'btc_basis': { target_apy: 0.08, max_drawdown: 0.02, description: 'Funding rate collection' },
  'eth_leveraged': { target_apy: 0.20, max_drawdown: 0.04, description: 'High risk, high reward' },
  'eth_staking_only': { target_apy: 0.03, max_drawdown: 0.01, description: 'Conservative staking' },
  'usdt_market_neutral': { target_apy: 0.15, max_drawdown: 0.04, description: 'Balanced risk/reward' },
  'usdt_market_neutral_no_leverage': { target_apy: 0.08, max_drawdown: 0.02, description: 'Lower risk market neutral' }
};

<ModeCard 
  mode="usdt_market_neutral"
  target_apy={modePerformance.usdt_market_neutral.target_apy}
  max_drawdown={modePerformance.usdt_market_neutral.max_drawdown}
  description={modePerformance.usdt_market_neutral.description}
  risk_level="medium" />
```

**Step 1: Share Class Selection**
```typescript
<WizardStep title="Choose Share Class">
  <ShareClassSelector>
    <Card value="USDT" 
          icon="💵"
          title="USDT (Stable)" 
          description="Market-neutral, returns in USD"
          complexity="Medium-High" />
    
    <Card value="ETH" 
          icon="💎"
          title="ETH (Directional)" 
          description="Long ETH, returns in ETH"
          complexity="Medium" />
  </ShareClassSelector>
</WizardStep>
```

**Step 2: Strategy Mode**
```typescript
<WizardStep title="Choose Strategy">
  {shareClass === 'USDT' && (
    <>
      <ModeCard mode="pure_lending" 
                icon="🏦" 
                apy="4-6%" 
                complexity="Simple" 
                description="Supply USDT to AAVE, earn interest" />
      
      <ModeCard mode="btc_basis" 
                icon="₿" 
                apy="5-10%" 
                complexity="Medium"
                description="Long BTC spot + short perp, earn funding" />
      
      <ModeCard mode="usdt_market_neutral" 
                icon="⚖️" 
                apy="8-15%" 
                complexity="Complex"
                description="Leveraged restaking with hedge" />
    </>
  )}
  
  {shareClass === 'ETH' && (
    <ModeCard mode="eth_leveraged" 
              icon="🔄" 
              apy="6-12%" 
              complexity="Medium"
              description="Leveraged ETH staking" />
  )}
</WizardStep>
```

**Step 3: Basic Configuration**
```typescript
<WizardStep title="Basic Settings">
  <NumberInput name="initial_capital" 
               label={shareClass === 'ETH' ? "Initial ETH" : "Initial USD"}
               min={shareClass === 'ETH' ? 10 : 10000}
               default={shareClass === 'ETH' ? 100 : 100000}
               validation={value => value > 0 ? null : "Must be positive"} />
  
  <DateRangeSelector name="period"
                     min="2024-01-01"
                     max="2025-09-18"
                     default={["2024-05-12", "2025-09-18"]} />
</WizardStep>
```

**Step 4: Strategy Parameters** (Mode-Specific)
```typescript
<WizardStep title="Strategy Configuration">
  {/* USDT Market-Neutral (most complex) */}
  {mode === 'usdt_market_neutral' && (
    <>
      <Select name="lst_type" 
              label="Staking Token"
              options={[
                {value: 'weeth', label: 'weETH (EtherFi - Restaking)'},
                {value: 'wsteth', label: 'wstETH (Lido - Classic)'}
              ]} />
      
      <Select name="rewards_mode"
              label="Rewards"
              options={[{value: 'base_only', label: 'Base Only'}]}
              disabled
              tooltip="USDT strategies only support base rewards" />
      
      <Checkbox name="use_flash_loan"
                label="Use Atomic Flash Loan"
                default={true}
                tooltip="Saves ~$150 gas vs sequential (~$200)" />
      
      <Slider name="target_ltv"
              label="Target LTV"
              min={0.5}
              max={0.92}
              default={0.91}
              step={0.01}
              marks={{0.91: 'Recommended', 0.93: 'Max'}} />
      
      <HedgeVenueSelector 
        venues={['binance', 'bybit', 'okx']}
        allocation={{binance: 33, bybit: 33, okx: 34}}
        label="Hedge Allocation (%)" />
    </>
  )}
  
  {/* Simpler modes have fewer parameters */}
  
  <EstimatedAPY mode={mode} config={formData} />
  {/* Shows: "Expected: 8-15% APY" based on mode + config */}
</WizardStep>
```

**Step 5: Review & Submit**
```typescript
<WizardStep title="Review Configuration">
  <ConfigSummary>
    <SummaryItem label="Mode" value={mode} />
    <SummaryItem label="Share Class" value={shareClass} />
    <SummaryItem label="Initial Capital" value={formatCurrency(initialCapital, shareClass)} />
    <SummaryItem label="Period" value={`${startDate} to ${endDate}`} />
    {/* ... all configured params */}
    <SummaryItem label="Estimated APY" value="8-15%" emphasis />
  </ConfigSummary>
  
  <Button onClick={submitBacktest} size="large">
    Run Backtest
  </Button>
</WizardStep>
```

---

## 📊 **Results Display**

### **Summary Metrics**

```typescript
<ResultsPage>
  <MetricCards>
    <MetricCard title="Total P&L"
                value={results.cumulative_pnl}
                currency={shareClass}
                change={results.pnl_pct}
                status={results.pnl > 0 ? 'positive' : 'negative'} />
    
    <MetricCard title="APY (Compounded)"
                value={`${results.apy_pct}%`}
                comparison={`vs ${results.ethena_apy}% Ethena`} />
    
    <MetricCard title="P&L Reconciliation"
                value={`$${results.reconciliation_diff}`}
                status={results.reconciliation_passed ? 'pass' : 'fail'}
                tooltip="Balance-based vs Attribution difference" />
    
    <MetricCard title="Max Drawdown"
                value={`${results.max_drawdown_pct}%`}
                status={results.max_drawdown_pct < 10 ? 'good' : 'warning'} />
    
    {/* Performance vs Targets */}
    {results.target_apy && (
      <MetricCard title="APY vs Target"
                  value={`${results.annualized_return_pct}% / ${results.target_apy * 100}%`}
                  status={results.apy_vs_target?.status === 'meets_target' ? 'good' : 'warning'}
                  tooltip={results.apy_vs_target?.message} />
    )}
    
    {results.target_max_drawdown && (
      <MetricCard title="Drawdown vs Target"
                  value={`${results.max_drawdown_pct}% / ${results.target_max_drawdown * 100}%`}
                  status={results.drawdown_vs_target?.status === 'within_target' ? 'good' : 'warning'}
                  tooltip={results.drawdown_vs_target?.message} />
    )}
    
    {/* Mode-specific metrics */}
    {mode === 'usdt_market_neutral' && (
      <>
        <MetricCard title="Final Health Factor" value={results.final_hf.toFixed(3)} />
        <MetricCard title="Min Margin Ratio" value={`${(results.min_margin_ratio * 100).toFixed(1)}%`} />
      </>
    )}
  </MetricCards>
</ResultsPage>
```

### **Charts Section** (Plotly HTML Embedded)

```typescript
<ChartsGrid>
  <PlotlyChart 
    html={results.plots.cumulative_pnl} 
    title="Cumulative P&L"
    fullscreenButton 
    downloadButton />
  
  {mode !== 'pure_lending' && (
    <PlotlyChart 
      html={results.plots.pnl_components}
      title="P&L Breakdown" />
  )}
  
  {mode === 'usdt_market_neutral' && (
    <>
      <PlotlyChart html={results.plots.delta_neutrality} title="Market Neutrality" />
      <PlotlyChart html={results.plots.margin_ratios} title="CEX Margin Ratios" />
      <PlotlyChart html={results.plots.risk_metrics} title="Risk Metrics" />
    </>
  )}
  
  <PlotlyChart html={results.plots.balance_sheet} title="Balance Sheet" />
  <PlotlyChart html={results.plots.drawdown} title="Drawdown" />
</ChartsGrid>
```

### **Event Log Viewer**

```typescript
<EventLogViewer>
  <EventFilters>
    <MultiSelect name="eventTypes"
                 options={['GAS_FEE_PAID', 'STAKE_DEPOSIT', 'COLLATERAL_SUPPLIED', ...]}
                 placeholder="Filter by event type" />
    
    <MultiSelect name="venues"
                 options={['ETHEREUM', 'AAVE', 'ETHERFI', 'BINANCE', 'BYBIT']}
                 placeholder="Filter by venue" />
    
    <DateRangeFilter name="dateRange" />
  </EventFilters>
  
  <VirtualizedTable
    data={filteredEvents}
    rowHeight={40}
    height={600}
    columns={[
      {key: 'timestamp', label: 'Time', width: 180},
      {key: 'order', label: 'Order', width: 80},
      {key: 'event_type', label: 'Event', width: 200},
      {key: 'venue', label: 'Venue', width: 120},
      {key: 'token', label: 'Token', width: 100},
      {key: 'amount', label: 'Amount', width: 150, format: 'number'},
      {key: 'expand', label: '', width: 50, render: ExpandButton}
    ]}
    expandableRow={EventDetails}  // Shows balance snapshots
  />
  
  <ExportButton onClick={exportFilteredEvents}>
    Export Filtered Events to CSV
  </ExportButton>
</EventLogViewer>
```

---

## 💻 **Component Structure** ✅ **WIZARD IMPLEMENTED, RESULTS MISSING**

```
frontend/src/
├── App.tsx                          # Main app with routing ✅ IMPLEMENTED
├── main.tsx                         # Entry point ✅ IMPLEMENTED
├── index.css                        # Tailwind imports ✅ IMPLEMENTED
│
├── components/
│   ├── wizard/                      # ✅ FULLY IMPLEMENTED
│   │   ├── WizardContainer.tsx     # Stepper logic ✅
│   │   ├── ShareClassStep.tsx      # Step 1 ✅
│   │   ├── ModeSelectionStep.tsx   # Step 2 ✅
│   │   ├── BasicConfigStep.tsx     # Step 3 ✅
│   │   ├── StrategyConfigStep.tsx  # Step 4 ✅
│   │   └── ReviewStep.tsx          # Step 5 ✅
│   │
│   ├── results/                     # ❌ NOT IMPLEMENTED
│   │   ├── MetricCard.tsx          # Summary metric display
│   │   ├── MetricCardsGrid.tsx     # Grid layout
│   │   ├── PlotlyChart.tsx         # Embed Plotly HTML
│   │   ├── ChartsGrid.tsx          # Chart layout
│   │   └── ResultsPage.tsx         # Full results view
│   │
│   ├── events/                      # ❌ NOT IMPLEMENTED
│   │   ├── EventLogViewer.tsx      # Main event log component
│   │   ├── EventFilters.tsx        # Filter controls
│   │   ├── VirtualizedTable.tsx    # Virtual scroll for 70k+ events
│   │   ├── EventRow.tsx            # Single event row
│   │   └── EventDetails.tsx        # Expandable balance snapshots
│   │
│   └── shared/                      # ❌ NOT IMPLEMENTED
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Select.tsx
│       ├── Checkbox.tsx
│       ├── Slider.tsx
│       └── Card.tsx
│
├── services/                        # ❌ NOT IMPLEMENTED
│   └── api.ts                       # API client
│
├── contexts/                        # ❌ NOT IMPLEMENTED
│   └── BacktestContext.tsx          # State management (React Context)
│
├── types/                           # ❌ NOT IMPLEMENTED
│   ├── backtest.ts                  # Backtest types
│   ├── results.ts                   # Results types
│   └── events.ts                    # Event types
│
└── utils/                           # ❌ NOT IMPLEMENTED
    ├── formatting.ts                # Number/currency formatting
    └── validation.ts                # Form validation
```

---

## 🔧 **Technology Stack**

**Framework**: React 18 + TypeScript + Vite  
**UI Library**: Tailwind CSS + shadcn/ui  
**State**: React Context (simple, sufficient)  
**Charts**: Plotly HTML (embedded from backend)  
**Tables**: react-virtual (virtualized scrolling for 70k+ events)  
**HTTP**: fetch API (native)  
**Forms**: React Hook Form (validation)

**Why This Stack**:
- Modern, lightweight
- Excellent wizard/stepper support (shadcn/ui)
- Mobile responsive (Tailwind)
- No bloat (minimal dependencies)
- Fast development

---

## 🎯 **Success Criteria**

### **✅ IMPLEMENTED (Wizard Components)**
- [x] Wizard flow intuitive (5 steps, clear progression)
- [x] Mode-specific forms show/hide correctly
- [x] Real-time validation works
- [x] Estimated APY displays before submit
- [x] Mobile responsive (desktop + mobile)
- [x] Fast load times (< 2s)

### **❌ NOT IMPLEMENTED (Results Components)**
- [ ] Results display all metrics
- [ ] Plotly charts embedded and interactive
- [ ] Event log handles 70k+ events (virtualized)
- [ ] Event filters work (type, venue, date)
- [ ] Balance snapshots expandable
- [ ] Download works (CSV, HTML, events)

### **🔧 IMPLEMENTATION NOTES**
- **Wizard Components**: Fully implemented with proper TypeScript interfaces and API integration
- **Results Components**: Missing - App.tsx references ResultsPage component that doesn't exist
- **API Integration**: ModeSelectionStep fetches modes from backend API successfully
- **State Management**: Uses React hooks for local state management
- **UI Framework**: Uses Tailwind CSS with Lucide React icons

### **🚧 CRITICAL MISSING COMPONENTS**
1. **ResultsPage**: Referenced in App.tsx but not implemented
2. **Results Components**: MetricCard, PlotlyChart, EventLogViewer, etc.
3. **Shared Components**: Button, Input, Select, etc. (using inline styles currently)
4. **API Service**: No centralized API client
5. **Type Definitions**: No TypeScript interfaces for results/events

---

**Status**: Wizard specification implemented! ✅ Results specification pending implementation ❌


