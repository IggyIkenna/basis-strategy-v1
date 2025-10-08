import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

// Mock the wizard components to avoid complex setup
vi.mock('./components/wizard/WizardContainer', () => ({
  WizardContainer: ({ onComplete, onCancel }: any) => (
    <div data-testid="wizard-container">
      <button onClick={() => onComplete({ mode: 'test', shareClass: 'USDT', initialCapital: 100000, startDate: '2024-01-01', endDate: '2024-12-31', strategyParams: {} })}>
        Complete Wizard
      </button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  )
}))

vi.mock('./components/results/ResultsPage', () => ({
  ResultsPage: ({ onBack, onNewBacktest }: any) => (
    <div data-testid="results-page">
      <button onClick={onBack}>Back to Wizard</button>
      <button onClick={onNewBacktest}>New Backtest</button>
    </div>
  )
}))

describe('App', () => {
  it('renders wizard initially', () => {
    render(<App />)
    expect(screen.getByTestId('wizard-container')).toBeInTheDocument()
  })

  it('switches to results after wizard completion', () => {
    render(<App />)
    
    // Complete the wizard
    screen.getByText('Complete Wizard').click()
    
    expect(screen.getByTestId('results-page')).toBeInTheDocument()
  })

  it('switches back to wizard from results', () => {
    render(<App />)
    
    // Complete the wizard
    screen.getByText('Complete Wizard').click()
    
    // Go back to wizard
    screen.getByText('Back to Wizard').click()
    
    expect(screen.getByTestId('wizard-container')).toBeInTheDocument()
  })

  it('starts new backtest from results', () => {
    render(<App />)
    
    // Complete the wizard
    screen.getByText('Complete Wizard').click()
    
    // Start new backtest
    screen.getByText('New Backtest').click()
    
    expect(screen.getByTestId('wizard-container')).toBeInTheDocument()
  })
})