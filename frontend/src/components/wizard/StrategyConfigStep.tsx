import React from 'react';
import { Settings, Info, AlertTriangle } from 'lucide-react';

interface StrategyConfigStepProps {
  mode: string;
  shareClass: 'USDT' | 'ETH';
  params: Record<string, any>;
  onUpdate: (params: Record<string, any>) => void;
}

export function StrategyConfigStep({ mode, shareClass, params, onUpdate }: StrategyConfigStepProps) {
  const getStrategyConfig = (mode: string, shareClass: 'USDT' | 'ETH') => {
    const baseConfigs = {
      pure_lending: {
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
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {strategyConfig.title}
        </h2>
        <p className="text-gray-600">
          {strategyConfig.description}
        </p>
      </div>

      <div className="space-y-6">
        {strategyConfig.fields.map((field) => (
          <div key={field.id} className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                {field.label}
              </label>
              <span className="text-sm text-gray-500">
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
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            
            <div className="flex justify-between text-xs text-gray-500">
              <span>{field.min}{field.type === 'number' && field.label.includes('%') ? '%' : ''}</span>
              <span>{field.max}{field.type === 'number' && field.label.includes('%') ? '%' : ''}</span>
            </div>
            
            <p className="text-xs text-gray-600">
              {field.description}
            </p>
          </div>
        ))}
      </div>

      {/* Info Panel */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <Info className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Strategy Parameters:</p>
            <ul className="space-y-1 text-blue-700">
              <li>• These parameters will be used to configure your strategy execution</li>
              <li>• You can adjust them based on your risk tolerance and market conditions</li>
              <li>• Higher values generally mean higher risk and potential returns</li>
              <li>• Consider backtesting with different parameter values to find optimal settings</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Current Configuration Summary */}
      <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex items-center mb-3">
          <Settings className="w-5 h-5 text-gray-600 mr-2" />
          <h3 className="text-sm font-medium text-gray-900">Current Configuration</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {strategyConfig.fields.map((field) => (
            <div key={field.id} className="flex justify-between text-sm">
              <span className="text-gray-600">{field.label}:</span>
              <span className="font-medium text-gray-900">
                {getFieldValue(field.id, field.default).toFixed(field.step < 1 ? 1 : 0)}
                {field.type === 'number' && field.label.includes('%') ? '%' : ''}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}