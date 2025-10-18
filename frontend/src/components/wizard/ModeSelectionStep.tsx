import { Check, Shield, Target, TrendingUp, Zap } from 'lucide-react';
import React, { useEffect, useState } from 'react';

interface ModeConfig {
  mode: string;
  description: string;
  target_apy: number;
  max_drawdown: number;
  share_class: string;
  risk_level: string;
  features: {
    lending_enabled: boolean;
    staking_enabled: boolean;
    leverage_enabled: boolean;
    basis_trade_enabled: boolean;
  };
}

interface ModeSelectionStepProps {
  shareClass: string;
  selectedMode: string;
  onSelect: (mode: string) => void;
}

export function ModeSelectionStep({ shareClass, selectedMode, onSelect }: ModeSelectionStepProps) {
  const [modes, setModes] = useState<ModeConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModes = async () => {
      try {
        setLoading(true);
        setError(null);

        // Try to use the API client (which will use mock if VITE_USE_MOCK_API=true)
        const { apiClient } = await import('../../services/api');
        // Convert share class to uppercase for API compatibility
        const upperShareClass = shareClass.toUpperCase();
        const modes = await apiClient.getModes(upperShareClass);
        setModes(modes);
      } catch (err) {
        console.error('Error fetching modes:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch modes');

        // Fallback to mock data if API fails
        try {
          const mockModes = await import('../../mocks/data/strategies/modes.json');
          setModes(mockModes.default || []);
          setError(null); // Clear error since we have fallback data
        } catch (mockErr) {
          console.error('Error loading mock data:', mockErr);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchModes();
  }, [shareClass]);

  const getIconForMode = (mode: string) => {
    switch (mode) {
      case 'pure_lending_usdt':
        return Shield;
      case 'btc_basis':
        return TrendingUp;
      case 'usdt_market_neutral':
        return Target;
      case 'eth_leveraged':
        return Zap;
      default:
        return Shield;
    }
  };

  const getFeaturesForMode = (config: ModeConfig) => {
    const features = [];
    if (config.features.lending_enabled) features.push('Lending enabled');
    if (config.features.staking_enabled) features.push('Staking enabled');
    if (config.features.leverage_enabled) features.push('Leverage enabled');
    if (config.features.basis_trade_enabled) features.push('Basis trading enabled');
    return features;
  };

  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400';
      case 'medium': return 'bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400';
      case 'high': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default: return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const getRiskIcon = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return '🟢';
      case 'medium': return '🟡';
      case 'high': return '🔴';
      default: return '⚪';
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent, mode: string) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(mode);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading strategy modes...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">Error Loading Modes</h2>
          <p className="text-slate-600 dark:text-slate-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 dark:from-slate-800 dark:to-slate-700 text-white">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2">
              Select Strategy Mode
            </h1>
            <p className="text-slate-300 text-lg">
              Choose the trading strategy that matches your risk tolerance
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="space-y-6">
          {modes.map((mode) => {
            const IconComponent = getIconForMode(mode.mode);
            const features = getFeaturesForMode(mode);
            return (
              <div
                key={mode.mode}
                role="radio"
                aria-checked={selectedMode === mode.mode}
                tabIndex={0}
                onClick={() => onSelect(mode.mode)}
                onKeyDown={(e) => handleKeyDown(e, mode.mode)}
                className={`
                  relative p-6 rounded-xl border-2 cursor-pointer transition-all duration-200
                  focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2
                  dark:focus:ring-offset-slate-900
                  ${selectedMode === mode.mode
                    ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/10 shadow-lg ring-2 ring-emerald-500/20'
                    : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-md'
                  }
                `}
              >
                <div className="flex items-start">
                  {/* Checkbox-like selection indicator */}
                  <div className="flex-shrink-0 mr-4 mt-1">
                    <div className={`
                      w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-200
                      ${selectedMode === mode.mode
                        ? 'bg-emerald-500 border-emerald-500'
                        : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800'
                      }
                    `}>
                      {selectedMode === mode.mode && (
                        <Check className="w-4 h-4 text-white" />
                      )}
                    </div>
                  </div>

                  {/* Icon and content */}
                  <div className="flex items-start flex-1">
                    <div className="flex-shrink-0 mr-4">
                      <div className={`
                        w-12 h-12 rounded-xl flex items-center justify-center
                        ${selectedMode === mode.mode
                          ? 'bg-emerald-500 text-white'
                          : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                        }
                      `}>
                        <IconComponent className="w-6 h-6" />
                      </div>
                    </div>

                    <div className="flex-1">
                      <h3 className={`
                        text-xl font-bold mb-2
                        ${selectedMode === mode.mode ? 'text-emerald-900 dark:text-emerald-100' : 'text-slate-900 dark:text-slate-100'}
                      `}>
                        {mode.mode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </h3>
                      <p className={`
                        text-sm mb-4
                        ${selectedMode === mode.mode ? 'text-emerald-700 dark:text-emerald-300' : 'text-slate-600 dark:text-slate-400'}
                      `}>
                        {mode.description || 'Advanced yield optimization strategy'}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 mb-4">
                        <span className={`
                          px-3 py-1 text-sm font-bold rounded-full flex items-center space-x-1
                          ${getRiskColor(mode.risk_level)}
                        `}>
                          <span>{getRiskIcon(mode.risk_level)}</span>
                          <span>{mode.risk_level.charAt(0).toUpperCase() + mode.risk_level.slice(1)} Risk</span>
                        </span>
                        <span className="text-sm font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400 px-3 py-1 rounded-full">
                          {(mode.target_apy * 100).toFixed(1)}% Target APY
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-700 px-3 py-1 rounded-full">
                          Max Drawdown: {(mode.max_drawdown * 100).toFixed(1)}%
                        </span>
                        <span className="text-xs text-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400 px-3 py-1 rounded-full">
                          Share Class: {mode.share_class}
                        </span>
                      </div>

                      <div className="space-y-2">
                        {features.map((feature, index) => (
                          <div key={index} className="flex items-center text-sm">
                            <div className={`
                              w-2 h-2 rounded-full mr-3
                              ${selectedMode === mode.mode ? 'bg-emerald-500' : 'bg-slate-400 dark:bg-slate-500'}
                            `} />
                            <span className={`
                              ${selectedMode === mode.mode ? 'text-emerald-700 dark:text-emerald-300' : 'text-slate-600 dark:text-slate-400'}
                            `}>
                              {feature}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selection Summary */}
        {selectedMode && (
          <div className="mt-8 p-6 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                  Selected Strategy Mode
                </p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {modes.find(m => m.mode === selectedMode)?.mode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  This strategy will be configured in the next steps with specific parameters and risk settings.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}