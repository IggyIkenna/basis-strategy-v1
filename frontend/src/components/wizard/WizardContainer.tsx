import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Check, TrendingUp } from 'lucide-react';
import { ShareClassStep } from './ShareClassStep';
import { ModeSelectionStep } from './ModeSelectionStep';
import { BasicConfigStep } from './BasicConfigStep';
import { StrategyConfigStep } from './StrategyConfigStep';
import { ReviewStep } from './ReviewStep';
import { apiClient } from '../../services/api';

export interface WizardConfig {
  shareClass: 'USDT' | 'ETH';
  mode: string;
  initialCapital: number;
  startDate: string;
  endDate: string;
  strategyParams: Record<string, any>;
  estimatedAPY?: number;
}

interface WizardContainerProps {
  onComplete?: (config: WizardConfig) => void;
  onCancel?: () => void;
  onShowResults?: (backtestId: string) => void;
}

const STEPS = [
  { id: 'shareClass', title: 'Share Class', description: 'Choose USDT or ETH' },
  { id: 'mode', title: 'Strategy Mode', description: 'Select trading strategy' },
  { id: 'basicConfig', title: 'Basic Config', description: 'Set capital and dates' },
  { id: 'strategyConfig', title: 'Strategy Params', description: 'Configure strategy' },
  { id: 'review', title: 'Review', description: 'Review and submit' }
];

export function WizardContainer({ onComplete, onCancel, onShowResults }: WizardContainerProps) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<Partial<WizardConfig>>({
    shareClass: 'USDT',
    mode: '',
    initialCapital: 100000,
    startDate: '',
    endDate: '',
    strategyParams: {}
  });

  const updateConfig = useCallback((updates: Partial<WizardConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  }, []);

  const nextStep = useCallback(() => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  }, [currentStep]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  const handleComplete = useCallback(async () => {
    if (config.shareClass && config.mode && config.initialCapital && config.startDate && config.endDate) {
      try {
        // Submit backtest to backend
        const backtestConfig = {
          mode_name: config.mode,
          share_class: config.shareClass.toLowerCase(),
          initial_capital: config.initialCapital,
          start_date: config.startDate,
          end_date: config.endDate,
          strategy_config: config.strategyParams
        };

        const response = await apiClient.runBacktest(backtestConfig);
        
        // Navigate to results page
        navigate(`/results/${response.request_id}`);
        
        // Call legacy callback if provided
        if (onShowResults) {
          onShowResults(response.request_id);
        } else if (onComplete) {
          onComplete(config as WizardConfig);
        }
      } catch (error) {
        console.error('Backtest submission failed:', error);
        alert(`Backtest failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  }, [config, navigate, onComplete, onShowResults]);

  const canProceed = useCallback(() => {
    switch (currentStep) {
      case 0: // Share Class
        return !!config.shareClass;
      case 1: // Mode Selection
        return !!config.mode;
      case 2: // Basic Config
        // Enhanced validation: check for valid values and reasonable ranges
        const capital = config.initialCapital || 0;
        const hasValidCapital = capital >= 1000 && capital <= 10000000;
        const hasValidDates = !!config.startDate && !!config.endDate;
        const startDate = new Date(config.startDate || '');
        const endDate = new Date(config.endDate || '');
        const hasValidDateRange = endDate > startDate && (endDate.getTime() - startDate.getTime()) >= 7 * 24 * 60 * 60 * 1000; // At least 7 days
        return hasValidCapital && hasValidDates && hasValidDateRange;
      case 3: // Strategy Config
        return Object.keys(config.strategyParams || {}).length > 0;
      case 4: // Review
        return true;
      default:
        return false;
    }
  }, [currentStep, config]);

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <ShareClassStep
            selectedClass={config.shareClass}
            onSelect={(shareClass) => updateConfig({ shareClass })}
          />
        );
      case 1:
        return (
          <ModeSelectionStep
            shareClass={config.shareClass!}
            selectedMode={config.mode}
            onSelect={(mode) => updateConfig({ mode })}
          />
        );
      case 2:
        return (
          <BasicConfigStep
            config={config}
            onUpdate={updateConfig}
          />
        );
      case 3:
        return (
          <StrategyConfigStep
            mode={config.mode!}
            shareClass={config.shareClass!}
            params={config.strategyParams || {}}
            onUpdate={(params) => updateConfig({ strategyParams: params })}
          />
        );
      case 4:
        return (
          <ReviewStep
            config={config as WizardConfig}
            onComplete={handleComplete}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
      <div className="max-w-5xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full mb-4">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
            DeFi Strategy Backtest Wizard
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Configure and run backtests for yield optimization strategies with real-time performance tracking
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-12">
          <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center justify-between">
              {STEPS.map((step, index) => (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex items-center">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold shadow-lg transition-all duration-300 ${
                        index <= currentStep
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white scale-110'
                          : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      {index < currentStep ? (
                        <Check className="w-6 h-6" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <div className="ml-4 hidden sm:block">
                      <p className={`text-sm font-semibold ${
                        index <= currentStep ? 'text-gray-900' : 'text-gray-400'
                      }`}>
                        {step.title}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                    </div>
                  </div>
                  {index < STEPS.length - 1 && (
                    <div className={`hidden sm:block flex-1 h-1 mx-6 rounded-full transition-all duration-300 ${
                      index < currentStep ? 'bg-gradient-to-r from-blue-600 to-purple-600' : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-10">
          {renderStep()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between mt-10">
          <button
            onClick={prevStep}
            disabled={currentStep === 0}
            className={`px-8 py-4 rounded-xl font-semibold transition-all duration-200 flex items-center space-x-2 ${
              currentStep === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300 hover:scale-105 shadow-md'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          <div className="flex space-x-4">
            <button
              onClick={onCancel}
              className="px-6 py-4 text-sm font-semibold text-gray-600 bg-white border-2 border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all duration-200"
            >
              Cancel
            </button>

            {currentStep < STEPS.length - 1 ? (
              <button
                onClick={nextStep}
                disabled={!canProceed()}
                className={`px-8 py-4 rounded-xl font-semibold transition-all duration-200 flex items-center space-x-2 ${
                  canProceed()
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 hover:scale-105 shadow-lg'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                <span>Next</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={!canProceed()}
                className={`px-8 py-4 rounded-xl font-semibold transition-all duration-200 flex items-center space-x-2 ${
                  canProceed()
                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-700 hover:to-emerald-700 hover:scale-105 shadow-lg'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                <span>Run Backtest</span>
                <TrendingUp className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}