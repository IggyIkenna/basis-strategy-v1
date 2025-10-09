import React, { useState, useEffect } from 'react';
import { Check, TrendingUp, Shield, Zap, Target } from 'lucide-react';

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
  shareClass: 'USDT' | 'ETH';
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
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
        const response = await fetch(`${API_BASE_URL}/strategies/modes/?share_class=${shareClass}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch modes: ${response.statusText}`);
        }
        const data = await response.json();
        if (data.success) {
          setModes(data.data.modes || []);
        } else {
          throw new Error(data.message || 'Failed to fetch modes');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch modes');
        console.error('Error fetching modes:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchModes();
  }, [shareClass]);

  const getIconForMode = (mode: string) => {
    switch (mode) {
      case 'pure_lending':
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
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
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

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Select Strategy Mode
          </h2>
          <p className="text-gray-600">
            Loading available strategies...
          </p>
        </div>
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Select Strategy Mode
          </h2>
          <p className="text-red-600">
            Error loading strategies: {error}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Select Strategy Mode
        </h2>
        <p className="text-gray-600">
          Choose the trading strategy that matches your risk tolerance
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {modes.map((mode) => {
          const IconComponent = getIconForMode(mode.mode);
          const features = getFeaturesForMode(mode);
          return (
            <div
              key={mode.mode}
              onClick={() => onSelect(mode.mode)}
              className={`relative p-8 border-2 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-xl ${
                selectedMode === mode.mode
                  ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-purple-50 shadow-lg scale-105'
                  : 'border-gray-200 hover:border-blue-300 bg-white shadow-md'
              }`}
            >
              {selectedMode === mode.mode && (
                <div className="absolute top-6 right-6">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                    <Check className="w-5 h-5 text-white" />
                  </div>
                </div>
              )}

              <div className="flex items-start mb-6">
                <div className={`p-4 rounded-2xl mr-6 ${
                  selectedMode === mode.mode 
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600' 
                    : 'bg-gray-100'
                }`}>
                  <IconComponent className={`w-8 h-8 ${
                    selectedMode === mode.mode ? 'text-white' : 'text-gray-600'
                  }`} />
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    {mode.mode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h3>
                  <p className="text-base text-gray-600 mb-4">
                    {mode.description || 'Advanced yield optimization strategy'}
                  </p>
                  <div className="flex items-center space-x-4 mb-3">
                    <span className={`px-3 py-1 text-sm font-bold rounded-full flex items-center space-x-1 ${getRiskColor(mode.risk_level)}`}>
                      <span>{getRiskIcon(mode.risk_level)}</span>
                      <span>{mode.risk_level.charAt(0).toUpperCase() + mode.risk_level.slice(1)} Risk</span>
                    </span>
                    <span className="text-lg font-bold text-green-600 bg-green-50 px-3 py-1 rounded-full">
                      {(mode.target_apy * 100).toFixed(1)}% Target APY
                    </span>
                  </div>
                  <div className="mb-4 flex items-center space-x-2">
                    <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                      Max Drawdown: {(mode.max_drawdown * 100).toFixed(1)}%
                    </span>
                    <span className="text-sm text-blue-500 bg-blue-50 px-3 py-1 rounded-full">
                      Share Class: {mode.share_class}
                    </span>
                  </div>
                </div>
              </div>

              <ul className="space-y-3">
                {features.map((feature, index) => (
                  <li key={index} className="flex items-center text-base text-gray-700">
                    <div className={`w-2 h-2 rounded-full mr-3 ${
                      selectedMode === mode.mode ? 'bg-blue-600' : 'bg-gray-400'
                    }`} />
                    <span className="font-medium">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      {selectedMode && (
        <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 rounded-2xl shadow-lg">
          <div className="flex items-center mb-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mr-3">
              <Check className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900">
              Strategy Selected
            </h3>
          </div>
          <p className="text-lg text-blue-800 mb-2">
            <strong>{modes.find(m => m.mode === selectedMode)?.mode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</strong>
          </p>
          <p className="text-base text-blue-700">
            This strategy will be configured in the next steps with specific parameters and risk settings.
          </p>
        </div>
      )}
    </div>
  );
}