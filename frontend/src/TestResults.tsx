import React from 'react';
import { ResultsPage } from './components/results';

const TestResults: React.FC = () => {
  // Mock backtest ID for testing
  const mockBacktestId = 'test-backtest-123';
  
  return (
    <div>
      <h1>Results Components Test</h1>
      <ResultsPage backtestId={mockBacktestId} />
    </div>
  );
};

export default TestResults;
