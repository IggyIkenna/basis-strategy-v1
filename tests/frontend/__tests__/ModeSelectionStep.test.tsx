import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ModeSelectionStep } from '../../../../frontend/src/components/wizard/ModeSelectionStep'

// Mock fetch
global.fetch = vi.fn()

describe('ModeSelectionStep', () => {
  const mockOnSelect = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    render(
      <ModeSelectionStep
        shareClass="USDT"
        selectedMode=""
        onSelect={mockOnSelect}
      />
    )

    expect(screen.getByText('Loading available strategies...')).toBeInTheDocument()
  })

  it('renders error state when API fails', async () => {
    ;(fetch as any).mockRejectedValueOnce(new Error('API Error'))

    render(
      <ModeSelectionStep
        shareClass="USDT"
        selectedMode=""
        onSelect={mockOnSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/Error loading strategies/)).toBeInTheDocument()
    })
  })

  it('renders modes when API succeeds', async () => {
    const mockModes = [
      {
        mode: 'pure_lending',
        description: 'Simple lending strategy',
        target_apy: 0.12,
        max_drawdown: 0.02,
        share_class: 'USDT',
        risk_level: 'low',
        features: {
          lending_enabled: true,
          staking_enabled: false,
          leverage_enabled: false,
          basis_trade_enabled: false
        }
      }
    ]

    ;(fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: { modes: mockModes }
      })
    })

    render(
      <ModeSelectionStep
        shareClass="USDT"
        selectedMode=""
        onSelect={mockOnSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Pure Lending')).toBeInTheDocument()
      expect(screen.getByText('12.0% Target APY')).toBeInTheDocument()
      expect(screen.getByText('Max Drawdown: 2.0%')).toBeInTheDocument()
    })
  })

  it('calls onSelect when mode is clicked', async () => {
    const mockModes = [
      {
        mode: 'pure_lending',
        description: 'Simple lending strategy',
        target_apy: 0.12,
        max_drawdown: 0.02,
        share_class: 'USDT',
        risk_level: 'low',
        features: {
          lending_enabled: true,
          staking_enabled: false,
          leverage_enabled: false,
          basis_trade_enabled: false
        }
      }
    ]

    ;(fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: { modes: mockModes }
      })
    })

    render(
      <ModeSelectionStep
        shareClass="USDT"
        selectedMode=""
        onSelect={mockOnSelect}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Pure Lending')).toBeInTheDocument()
    })

    screen.getByText('Pure Lending').click()
    expect(mockOnSelect).toHaveBeenCalledWith('pure_lending')
  })
})