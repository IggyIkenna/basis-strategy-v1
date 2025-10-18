import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../services/api';
import { BasicConfigStep } from './BasicConfigStep';
import { InstitutionalModeSelectionStep } from './InstitutionalModeSelectionStep';
import { InstitutionalShareClassStep } from './InstitutionalShareClassStep';
import { ReviewStep } from './ReviewStep';
import { StrategyConfigStep } from './StrategyConfigStep';

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
          <InstitutionalShareClassStep
            selected={config.shareClass}
            onSelect={(shareClass) => updateConfig({ shareClass })}
            onNext={nextStep}
            onBack={currentStep > 0 ? prevStep : undefined}
          />
        );
      case 1:
        return (
          <InstitutionalModeSelectionStep
            shareClass={config.shareClass!}
            selectedMode={config.mode}
            onSelect={(mode) => updateConfig({ mode })}
            onNext={nextStep}
            onBack={currentStep > 0 ? prevStep : undefined}
          />
        );
      case 2:
        return (
          <BasicConfigStep
            config={config}
            onUpdate={updateConfig}
            onNext={nextStep}
            onBack={currentStep > 0 ? prevStep : undefined}
          />
        );
      case 3:
        return (
          <StrategyConfigStep
            mode={config.mode!}
            shareClass={config.shareClass!}
            params={config.strategyParams || {}}
            onUpdate={(params) => updateConfig({ strategyParams: params })}
            onNext={nextStep}
            onBack={currentStep > 0 ? prevStep : undefined}
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
    <div>
      {renderStep()}
    </div>
  );
}