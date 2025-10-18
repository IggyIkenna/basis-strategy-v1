import React from 'react';
import { CheckCircle, AlertCircle, Clock, DollarSign, TrendingUp, Settings, ArrowLeft, ArrowRight } from 'lucide-react';

interface ReviewStepProps {
  config: {
    shareClass: 'USDT' | 'ETH';
    mode: string;
    initialCapital: number;
    startDate: string;
    endDate: string;
    strategyParams: Record<string, any>;
    estimatedAPY?: number;
  };
  onComplete: () => void;
  onBack?: () => void;
}

export function ReviewStep({ config, onComplete, onBack }: ReviewStepProps) {
  const getModeDisplayName = (mode: string) => {
    const modeNames: Record<string, string> = {
      pure_lending_usdt: 'Pure Lending',
      btc_basis: 'BTC Basis Trading',
      usdt_market_neutral: 'USDT Market Neutral',
      eth_leveraged: 'ETH Leveraged'
    };
    return modeNames[mode] || mode;
  };

  const getRiskLevel = (mode: string) => {
    const riskLevels: Record<string, { level: string; color: string; description: string }> = {
      pure_lending_usdt: { level: 'Low', color: 'text-green-600 bg-green-100', description: 'Conservative strategy with minimal risk' },
      btc_basis: { level: 'Medium', color: 'text-yellow-600 bg-yellow-100', description: 'Moderate risk with basis trading' },
      usdt_market_neutral: { level: 'Medium', color: 'text-yellow-600 bg-yellow-100', description: 'Balanced risk-return profile' },
      eth_leveraged: { level: 'High', color: 'text-red-600 bg-red-100', description: 'High risk with leveraged positions' }
    };
    return riskLevels[mode] || { level: 'Unknown', color: 'text-gray-600 bg-gray-100', description: 'Risk level not determined' };
  };

  const getEstimatedAPY = (mode: string) => {
    const apyEstimates: Record<string, string> = {
      pure_lending_usdt: '8-12%',
      btc_basis: '15-25%',
      usdt_market_neutral: '12-18%',
      eth_leveraged: '20-35%'
    };
    return apyEstimates[mode] || 'Variable';
  };

  const riskInfo = getRiskLevel(config.mode);
  const estimatedAPY = getEstimatedAPY(config.mode);

  const calculateBacktestDuration = () => {
    const start = new Date(config.startDate);
    const end = new Date(config.endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const backtestDuration = calculateBacktestDuration();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 dark:from-slate-800 dark:to-slate-700 text-white">
        <div className="max-w-4xl mx-auto px-6 py-12">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-2">
                Review Your Configuration
              </h1>
              <p className="text-slate-300 text-lg">
                Please review your strategy configuration before proceeding
              </p>
            </div>
            {onBack && (
              <button
                onClick={onBack}
                className="text-slate-300 hover:text-white transition-colors"
                aria-label="Go back"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="space-y-8">

          {/* Configuration Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Basic Configuration */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mr-4">
                  <DollarSign className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Basic Configuration
                </h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Share Class:</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">{config.shareClass}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Initial Capital:</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {config.initialCapital.toLocaleString()} {config.shareClass}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Backtest Period:</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">{backtestDuration} days</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Start Date:</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">{config.startDate}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">End Date:</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">{config.endDate}</span>
                </div>
              </div>
            </div>

            {/* Strategy Configuration */}
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 flex items-center justify-center mr-4">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Strategy Configuration
                </h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Strategy Mode:</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">{getModeDisplayName(config.mode)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Risk Level:</span>
                  <span className={`px-3 py-1 text-sm font-bold rounded-full ${riskInfo.color}`}>
                    {riskInfo.level}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Estimated APY:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">{estimatedAPY}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Parameters:</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {Object.keys(config.strategyParams).length} configured
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Strategy Parameters */}
          {Object.keys(config.strategyParams).length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 flex items-center justify-center mr-4">
                  <Settings className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Strategy Parameters
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(config.strategyParams).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <span className="text-slate-600 dark:text-slate-400 font-medium capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}:
                    </span>
                    <span className="font-bold text-slate-900 dark:text-slate-100">
                      {typeof value === 'number' ? value.toFixed(1) : value}
                      {key.includes('Rate') || key.includes('Threshold') || key.includes('Loss') || key.includes('Profit') ? '%' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

      {/* Risk Warning */}
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">Risk Disclaimer:</p>
            <ul className="space-y-1 text-yellow-700">
              <li>• This is a backtest simulation and past performance does not guarantee future results</li>
              <li>• {riskInfo.description}</li>
              <li>• Market conditions can change rapidly and affect strategy performance</li>
              <li>• Always consider your risk tolerance before implementing any strategy</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Performance Expectations */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <Clock className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">What to Expect:</p>
            <ul className="space-y-1 text-blue-700">
              <li>• Backtest will simulate {backtestDuration} days of trading</li>
              <li>• Results will include P&L, drawdown, and performance metrics</li>
              <li>• Strategy will be tested against historical market data</li>
              <li>• Execution time may vary based on strategy complexity</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Final Confirmation */}
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <CheckCircle className="w-8 h-8 text-green-500 mr-2" />
          <span className="text-lg font-medium text-gray-900">
            Ready to Start Backtest
          </span>
        </div>
        <p className="text-gray-600 mb-6">
          Click "Complete Setup" to begin the backtest with your configured strategy.
        </p>
        <button
          onClick={onComplete}
          className="px-8 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors"
        >
          Complete Setup & Start Backtest
        </button>
      </div>
    </div>
  );
}