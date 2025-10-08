import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MetricCard } from '../MetricCard'

describe('MetricCard', () => {
  it('renders basic metric card', () => {
    render(
      <MetricCard
        title="Test Metric"
        value="100.00"
        status="neutral"
      />
    )

    expect(screen.getByText('Test Metric')).toBeInTheDocument()
    expect(screen.getByText('100.00')).toBeInTheDocument()
  })

  it('renders success status correctly', () => {
    render(
      <MetricCard
        title="Success Metric"
        value="95.5"
        status="success"
      />
    )

    expect(screen.getByText('Success Metric')).toBeInTheDocument()
    expect(screen.getByText('95.5')).toBeInTheDocument()
  })

  it('renders warning status correctly', () => {
    render(
      <MetricCard
        title="Warning Metric"
        value="75.0"
        status="warning"
      />
    )

    expect(screen.getByText('Warning Metric')).toBeInTheDocument()
    expect(screen.getByText('75.0')).toBeInTheDocument()
  })

  it('renders error status correctly', () => {
    render(
      <MetricCard
        title="Error Metric"
        value="25.0"
        status="error"
      />
    )

    expect(screen.getByText('Error Metric')).toBeInTheDocument()
    expect(screen.getByText('25.0')).toBeInTheDocument()
  })

  it('renders comparison data when provided', () => {
    render(
      <MetricCard
        title="Comparison Metric"
        value="80.0"
        status="neutral"
        comparison={{
          actual: 80.0,
          target: 75.0,
          difference: 5.0
        }}
      />
    )

    expect(screen.getByText('Actual:')).toBeInTheDocument()
    expect(screen.getByText('80.00')).toBeInTheDocument()
    expect(screen.getByText('Target:')).toBeInTheDocument()
    expect(screen.getByText('75.00')).toBeInTheDocument()
    expect(screen.getByText('Difference:')).toBeInTheDocument()
    expect(screen.getByText('+5.00')).toBeInTheDocument()
  })

  it('renders tooltip when provided', () => {
    render(
      <MetricCard
        title="Tooltip Metric"
        value="50.0"
        status="neutral"
        tooltip="This is a test tooltip"
      />
    )

    expect(screen.getByText('This is a test tooltip')).toBeInTheDocument()
  })
})