import { Check, Shield, Zap } from 'lucide-react';
import React from 'react';

interface ShareClass {
  id: 'USDT' | 'ETH';
  name: string;
  description: string;
  features: string[];
  icon: React.ReactNode;
  riskLevel: 'Low' | 'Medium' | 'High';
  targetApy: string;
}

interface ShareClassStepProps {
  selectedClass: 'USDT' | 'ETH';
  onSelect: (shareClass: 'USDT' | 'ETH') => void;
}

export function ShareClassStep({ selectedClass, onSelect }: ShareClassStepProps) {
  const shareClasses: ShareClass[] = [
    {
      id: 'USDT',
      name: 'USDT Share Class',
      description: 'Stable value reference for conservative strategies',
      features: [
        'Stable value reference',
        'Lower volatility exposure',
        'Conservative risk profile',
        'Suitable for institutional clients'
      ],
      icon: <Shield className="w-6 h-6" />,
      riskLevel: 'Low',
      targetApy: '5-8%'
    },
    {
      id: 'ETH',
      name: 'ETH Share Class',
      description: 'Higher potential returns with ETH price exposure',
      features: [
        'Higher potential returns',
        'ETH price exposure',
        'Aggressive risk profile',
        'Suitable for growth strategies'
      ],
      icon: <Zap className="w-6 h-6" />,
      riskLevel: 'High',
      targetApy: '8-15%'
    }
  ];

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low': return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400';
      case 'Medium': return 'bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400';
      case 'High': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default: return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent, shareClass: 'USDT' | 'ETH') => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(shareClass);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 dark:from-slate-800 dark:to-slate-700 text-white">
        <div className="max-w-4xl mx-auto px-6 py-12">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2">
              Choose Your Share Class
            </h1>
            <p className="text-slate-300 text-lg">
              Select the base currency for your trading strategy
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {shareClasses.map((shareClass) => (
            <div
              key={shareClass.id}
              role="radio"
              aria-checked={selectedClass === shareClass.id}
              tabIndex={0}
              onClick={() => onSelect(shareClass.id)}
              onKeyDown={(e) => handleKeyDown(e, shareClass.id)}
              className={`
                relative p-8 rounded-xl border-2 cursor-pointer transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2
                dark:focus:ring-offset-slate-900
                ${selectedClass === shareClass.id
                  ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/10 shadow-lg ring-2 ring-emerald-500/20'
                  : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-md'
                }
              `}
            >
              {/* Selection Indicator */}
              <div className="absolute top-6 right-6">
                <div className={`
                  w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-200
                  ${selectedClass === shareClass.id
                    ? 'bg-emerald-500 border-emerald-500'
                    : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800'
                  }
                `}>
                  {selectedClass === shareClass.id && (
                    <Check className="w-4 h-4 text-white" />
                  )}
                </div>
              </div>

              {/* Icon and Header */}
              <div className="flex items-start mb-6">
                <div className={`
                  w-12 h-12 rounded-xl flex items-center justify-center mr-4 transition-colors
                  ${selectedClass === shareClass.id
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                  }
                `}>
                  {shareClass.icon}
                </div>
                <div className="flex-1">
                  <h3 className={`
                    text-2xl font-bold mb-2
                    ${selectedClass === shareClass.id
                      ? 'text-emerald-900 dark:text-emerald-100'
                      : 'text-slate-900 dark:text-slate-100'
                    }
                  `}>
                    {shareClass.name}
                  </h3>
                  <p className={`
                    text-sm mb-4
                    ${selectedClass === shareClass.id
                      ? 'text-emerald-700 dark:text-emerald-300'
                      : 'text-slate-600 dark:text-slate-400'
                    }
                  `}>
                    {shareClass.description}
                  </p>
                </div>
              </div>

              {/* Risk and APY Badges */}
              <div className="flex items-center gap-3 mb-6">
                <span className={`
                  px-3 py-1 text-xs font-semibold rounded-full
                  ${getRiskColor(shareClass.riskLevel)}
                `}>
                  {shareClass.riskLevel} Risk
                </span>
                <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400">
                  {shareClass.targetApy} Target APY
                </span>
              </div>

              {/* Features List */}
              <div className="space-y-3">
                {shareClass.features.map((feature, index) => (
                  <div key={index} className="flex items-center text-sm">
                    <div className={`
                      w-2 h-2 rounded-full mr-3 flex-shrink-0
                      ${selectedClass === shareClass.id
                        ? 'bg-emerald-500'
                        : 'bg-slate-400 dark:bg-slate-500'
                      }
                    `} />
                    <span className={`
                      ${selectedClass === shareClass.id
                        ? 'text-emerald-700 dark:text-emerald-300'
                        : 'text-slate-600 dark:text-slate-400'
                      }
                    `}>
                      {feature}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Selection Summary */}
        {selectedClass && (
          <div className="mb-8 p-6 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                  Selected Share Class
                </p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {shareClasses.find(sc => sc.id === selectedClass)?.name}
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  This choice will affect the available strategy modes and risk parameters.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}