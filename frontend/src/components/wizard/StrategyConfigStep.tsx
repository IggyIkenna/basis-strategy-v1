import React from 'react';
import { Settings, Info, AlertTriangle, ArrowLeft, ArrowRight } from 'lucide-react';

interface StrategyConfigStepProps {
  mode: string;
  shareClass: 'USDT' | 'ETH';
  params: Record<string, any>;
  onUpdate: (params: Record<string, any>) => void;
  onNext?: () => void;
  onBack?: () => void;
}

export function StrategyConfigStep({ mode, shareClass, params, onUpdate, onNext, onBack }: StrategyConfigStepProps) {
  const getStrategyConfig = (mode: string, shareClass: 'USDT' | 'ETH') => {
    const baseConfigs = {
      pure_lending_usdt: {
        title: 'Pure Lending Configuration',
        description: 'Configure lending parameters for stable yield generation',
        fields: [
          {
            id: 'lendingRate',
            label: 'Target Lending Rate (%)',
            type: 'number',
            min: 0.1,
            max: 50,
            step: 0.1,
            default: 8.5,
            description: 'Target annual lending rate'
          },
          {
            id: 'maxLendingRatio',
            label: 'Max Lending Ratio',
            type: 'number',
            min: 0.1,
            max: 1,
            step: 0.05,
            default: 0.8,
            description: 'Maximum portion of capital to lend'
          }
        ]
      },
      btc_basis: {
        title: 'BTC Basis Trading Configuration',
        description: 'Configure BTC futures basis trading parameters',
        fields: [
          {
            id: 'basisThreshold',
            label: 'Basis Threshold (%)',
            type: 'number',
            min: 0.1,
            max: 10,
            step: 0.1,
            default: 2.0,
            description: 'Minimum basis spread to trigger trade'
          },
          {
            id: 'maxPositionSize',
            label: 'Max Position Size (%)',
            type: 'number',
            min: 0.1,
            max: 1,
            step: 0.05,
            default: 0.3,
            description: 'Maximum position size relative to capital'
          },
          {
            id: 'leverage',
            label: 'Leverage',
            type: 'number',
            min: 1,
            max: 10,
            step: 0.5,
            default: 2,
            description: 'Trading leverage multiplier'
          }
        ]
      }
    };

    if (shareClass === 'USDT') {
      return {
        ...baseConfigs,
        usdt_market_neutral: {
          title: 'USDT Market Neutral Configuration',
          description: 'Configure market-neutral USDT strategy parameters',
          fields: [
            {
              id: 'neutralityThreshold',
              label: 'Neutrality Threshold (%)',
              type: 'number',
              min: 0.1,
              max: 5,
              step: 0.1,
              default: 1.0,
              description: 'Maximum allowed market exposure'
            },
            {
              id: 'rebalanceFrequency',
              label: 'Rebalance Frequency (hours)',
              type: 'number',
              min: 1,
              max: 168,
              step: 1,
              default: 24,
              description: 'How often to rebalance positions'
            }
          ]
        }
      };
    } else {
      return {
        ...baseConfigs,
        eth_leveraged: {
          title: 'ETH Leveraged Configuration',
          description: 'Configure leveraged ETH trading parameters',
          fields: [
            {
              id: 'leverage',
              label: 'Leverage',
              type: 'number',
              min: 1,
              max: 20,
              step: 0.5,
              default: 3,
              description: 'Trading leverage multiplier'
            },
            {
              id: 'stopLoss',
              label: 'Stop Loss (%)',
              type: 'number',
              min: 1,
              max: 50,
              step: 1,
              default: 15,
              description: 'Stop loss percentage'
            },
            {
              id: 'takeProfit',
              label: 'Take Profit (%)',
              type: 'number',
              min: 1,
              max: 100,
              step: 1,
              default: 30,
              description: 'Take profit percentage'
            }
          ]
        }
      };
    }
  };

  const strategyConfig = getStrategyConfig(mode, shareClass)[mode as keyof ReturnType<typeof getStrategyConfig>];

  if (!strategyConfig) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Configuration Not Available
        </h3>
        <p className="text-gray-600">
          Strategy configuration for {mode} is not available for {shareClass} share class.
        </p>
      </div>
    );
  }

  const handleFieldChange = (fieldId: string, value: number) => {
    onUpdate({
      ...params,
      [fieldId]: value
    });
  };

  const getFieldValue = (fieldId: string, defaultValue: number) => {
    return params[fieldId] !== undefined ? params[fieldId] : defaultValue;
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 dark:from-slate-800 dark:to-slate-700 text-white">
        <div className="max-w-4xl mx-auto px-6 py-12">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-2">
                {strategyConfig.title}
              </h1>
              <p className="text-slate-300 text-lg">
                {strategyConfig.description}
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

          <div className="space-y-8">
            {strategyConfig.fields.map((field) => (
              <div key={field.id} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <label className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {field.label}
                  </label>
                  <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                    {getFieldValue(field.id, field.default).toFixed(field.step < 1 ? 1 : 0)}
                    {field.type === 'number' && field.label.includes('%') ? '%' : ''}
                  </span>
                </div>
                
                <input
                  type="range"
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={getFieldValue(field.id, field.default)}
                  onChange={(e) => handleFieldChange(field.id, parseFloat(e.target.value))}
                  className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer slider focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  style={{
                    background: `linear-gradient(to right, #10b981 0%, #10b981 ${((getFieldValue(field.id, field.default) - field.min) / (field.max - field.min)) * 100}%, #e2e8f0 ${((getFieldValue(field.id, field.default) - field.min) / (field.max - field.min)) * 100}%, #e2e8f0 100%)`
                  }}
                />
                
                <div className="flex justify-between text-sm text-slate-500 dark:text-slate-400 mt-2">
                  <span>{field.min}{field.type === 'number' && field.label.includes('%') ? '%' : ''}</span>
                  <span>{field.max}{field.type === 'number' && field.label.includes('%') ? '%' : ''}</span>
                </div>
                
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-3">
                  {field.description}
                </p>
              </div>
            ))}
          </div>

          {/* Info Panel */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
            <div className="flex items-start">
              <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center mr-3 mt-0.5">
                <Info className="w-5 h-5" />
              </div>
              <div className="text-sm">
                <p className="font-semibold text-blue-900 dark:text-blue-100 mb-2">Strategy Parameters:</p>
                <ul className="space-y-2 text-blue-800 dark:text-blue-200">
                  <li className="flex items-start">
                    <div className="w-2 h-2 rounded-full bg-blue-500 mr-3 mt-2 flex-shrink-0"></div>
                    <span>These parameters will be used to configure your strategy execution</span>
                  </li>
                  <li className="flex items-start">
                    <div className="w-2 h-2 rounded-full bg-blue-500 mr-3 mt-2 flex-shrink-0"></div>
                    <span>You can adjust them based on your risk tolerance and market conditions</span>
                  </li>
                  <li className="flex items-start">
                    <div className="w-2 h-2 rounded-full bg-blue-500 mr-3 mt-2 flex-shrink-0"></div>
                    <span>Higher values generally mean higher risk and potential returns</span>
                  </li>
                  <li className="flex items-start">
                    <div className="w-2 h-2 rounded-full bg-blue-500 mr-3 mt-2 flex-shrink-0"></div>
                    <span>Consider backtesting with different parameter values to find optimal settings</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Current Configuration Summary */}
          <div className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6">
            <div className="flex items-center mb-4">
              <div className="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400 flex items-center justify-center mr-3">
                <Settings className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Current Configuration</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {strategyConfig.fields.map((field) => (
                <div key={field.id} className="flex justify-between items-center p-3 bg-white dark:bg-slate-700 rounded-lg">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">{field.label}:</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {getFieldValue(field.id, field.default).toFixed(field.step < 1 ? 1 : 0)}
                    {field.type === 'number' && field.label.includes('%') ? '%' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {onBack && (
                <button
                  onClick={onBack}
                  className="px-6 py-3 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors flex items-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Previous
                </button>
              )}
            </div>

            {onNext && (
              <button
                onClick={onNext}
                className="px-8 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg transition-all duration-200 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                Continue
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}