import React, { useState, useEffect } from 'react';
import { DollarSign, Calendar, Info, CheckCircle, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react';

interface BasicConfigStepProps {
  config: Partial<{
    shareClass: 'USDT' | 'ETH';
    mode: string;
    initialCapital: number;
    startDate: string;
    endDate: string;
    strategyParams: Record<string, any>;
  }>;
  onUpdate: (updates: Partial<{
    shareClass: 'USDT' | 'ETH';
    mode: string;
    initialCapital: number;
    startDate: string;
    endDate: string;
    strategyParams: Record<string, any>;
  }>) => void;
  onNext?: () => void;
  onBack?: () => void;
}

export function BasicConfigStep({ config, onUpdate, onNext, onBack }: BasicConfigStepProps) {
  const [validation, setValidation] = useState({
    capital: { isValid: false, message: '' },
    startDate: { isValid: false, message: '' },
    endDate: { isValid: false, message: '' },
    overall: { isValid: false, message: '' }
  });

  const validateCapital = (value: number) => {
    if (!value || value <= 0) {
      return { isValid: false, message: 'Capital must be greater than 0' };
    }
    if (value < 1000) {
      return { isValid: false, message: 'Minimum capital is 1,000' };
    }
    if (value > 10000000) {
      return { isValid: false, message: 'Maximum capital is 10,000,000' };
    }
    return { isValid: true, message: 'Valid capital amount' };
  };

  const validateDate = (date: string, type: 'start' | 'end') => {
    if (!date) {
      return { isValid: false, message: `${type} date is required` };
    }
    
    const dateObj = new Date(date);
    const today = new Date();
    const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
    
    if (dateObj > today) {
      return { isValid: false, message: `${type} date cannot be in the future` };
    }
    if (dateObj < oneYearAgo) {
      return { isValid: false, message: `${type} date must be within the last year` };
    }
    
    if (type === 'end' && config.startDate) {
      const startDate = new Date(config.startDate);
      if (dateObj <= startDate) {
        return { isValid: false, message: 'End date must be after start date' };
      }
      const diffDays = Math.ceil((dateObj.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
      if (diffDays < 7) {
        return { isValid: false, message: 'Backtest period must be at least 7 days' };
      }
    }
    
    return { isValid: true, message: 'Valid date' };
  };

  useEffect(() => {
    const capitalValidation = validateCapital(config.initialCapital || 0);
    const startDateValidation = validateDate(config.startDate || '', 'start');
    const endDateValidation = validateDate(config.endDate || '', 'end');
    
    const overallValid = capitalValidation.isValid && startDateValidation.isValid && endDateValidation.isValid;
    
    setValidation({
      capital: capitalValidation,
      startDate: startDateValidation,
      endDate: endDateValidation,
      overall: { isValid: overallValid, message: overallValid ? 'Configuration is valid' : 'Please fix the errors above' }
    });
  }, [config.initialCapital, config.startDate, config.endDate]);

  const handleCapitalChange = (value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue > 0) {
      onUpdate({ initialCapital: numValue });
    }
  };

  const handleDateChange = (field: 'startDate' | 'endDate', value: string) => {
    onUpdate({ [field]: value });
  };

  const getMinDate = () => {
    const today = new Date();
    const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
    return oneYearAgo.toISOString().split('T')[0];
  };

  const getMaxDate = () => {
    return new Date().toISOString().split('T')[0];
  };

  const getCapitalSuggestions = () => {
    const base = config.shareClass === 'USDT' ? 100000 : 10;
    return [
      base,
      base * 2,
      base * 5,
      base * 10
    ];
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 dark:from-slate-800 dark:to-slate-700 text-white">
        <div className="max-w-4xl mx-auto px-6 py-12">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-2">
                Basic Configuration
              </h1>
              <p className="text-slate-300 text-lg">
                Set your initial capital and backtest period
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Initial Capital */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mr-4">
                <DollarSign className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Initial Capital
                </h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Set your starting capital in {config.shareClass}
                </p>
              </div>
            </div>
          
            <div className="space-y-4">
              <div className="relative">
                <input
                  type="number"
                  value={config.initialCapital || ''}
                  onChange={(e) => handleCapitalChange(e.target.value)}
                  placeholder={`Enter amount in ${config.shareClass}`}
                  className={`w-full px-4 py-3 pr-12 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-colors ${
                    validation.capital.isValid 
                      ? 'border-emerald-300 bg-emerald-50 dark:bg-emerald-900/10' 
                      : config.initialCapital 
                        ? 'border-red-300 bg-red-50 dark:bg-red-900/10' 
                        : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700'
                  }`}
                  min="0"
                  step="0.01"
                />
                {config.initialCapital && (
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                    {validation.capital.isValid ? (
                      <CheckCircle className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                )}
              </div>
              {config.initialCapital && (
                <p className={`text-sm ${
                  validation.capital.isValid ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {validation.capital.message}
                </p>
              )}
            
              <div className="grid grid-cols-2 gap-3">
                {getCapitalSuggestions().map((amount) => (
                  <button
                    key={amount}
                    onClick={() => onUpdate({ initialCapital: amount })}
                    className={`px-4 py-3 text-sm font-medium rounded-lg border-2 transition-all duration-200 ${
                      config.initialCapital === amount
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400'
                        : 'bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600'
                    }`}
                  >
                    {amount.toLocaleString()} {config.shareClass}
                  </button>
                ))}
              </div>
          </div>
        </div>

          {/* Date Range */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 flex items-center justify-center mr-4">
                <Calendar className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Backtest Period
                </h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Set the time range for your backtest
                </p>
              </div>
            </div>
          
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Start Date</label>
                <div className="relative">
                  <input
                    type="date"
                    value={config.startDate || ''}
                    onChange={(e) => handleDateChange('startDate', e.target.value)}
                    min={getMinDate()}
                    max={getMaxDate()}
                    className={`w-full px-4 py-3 pr-12 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-colors ${
                      validation.startDate.isValid 
                        ? 'border-emerald-300 bg-emerald-50 dark:bg-emerald-900/10' 
                        : config.startDate 
                          ? 'border-red-300 bg-red-50 dark:bg-red-900/10' 
                          : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700'
                    }`}
                  />
                  {config.startDate && (
                    <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                      {validation.startDate.isValid ? (
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
                {config.startDate && (
                  <p className={`text-sm mt-2 ${
                    validation.startDate.isValid ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {validation.startDate.message}
                  </p>
                )}
              </div>
            
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">End Date</label>
                <div className="relative">
                  <input
                    type="date"
                    value={config.endDate || ''}
                    onChange={(e) => handleDateChange('endDate', e.target.value)}
                    min={config.startDate || getMinDate()}
                    max={getMaxDate()}
                    className={`w-full px-4 py-3 pr-12 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-colors ${
                      validation.endDate.isValid 
                        ? 'border-emerald-300 bg-emerald-50 dark:bg-emerald-900/10' 
                        : config.endDate 
                          ? 'border-red-300 bg-red-50 dark:bg-red-900/10' 
                          : 'border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700'
                    }`}
                  />
                  {config.endDate && (
                    <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                      {validation.endDate.isValid ? (
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
                {config.endDate && (
                  <p className={`text-sm mt-2 ${
                    validation.endDate.isValid ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {validation.endDate.message}
                  </p>
                )}
              </div>
          </div>
        </div>
      </div>

        {/* Info Panel */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
          <div className="flex items-start">
            <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center mr-3 mt-0.5">
              <Info className="w-5 h-5" />
            </div>
            <div className="text-sm">
              <p className="font-semibold text-blue-900 dark:text-blue-100 mb-2">Configuration Notes:</p>
              <ul className="space-y-2 text-blue-800 dark:text-blue-200">
                <li className="flex items-start">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mr-3 mt-2 flex-shrink-0"></div>
                  <span>Capital amount determines your position sizes and risk exposure</span>
                </li>
                <li className="flex items-start">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mr-3 mt-2 flex-shrink-0"></div>
                  <span>Backtest period should be at least 30 days for meaningful results</span>
                </li>
                <li className="flex items-start">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mr-3 mt-2 flex-shrink-0"></div>
                  <span>Historical data availability may limit your date range</span>
                </li>
                <li className="flex items-start">
                  <div className="w-2 h-2 rounded-full bg-blue-500 mr-3 mt-2 flex-shrink-0"></div>
                  <span>Strategy performance can vary significantly across different time periods</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Validation Summary */}
        <div className={`p-6 border-2 rounded-xl ${
          validation.overall.isValid 
            ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800' 
            : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
        }`}>
          <div className="flex items-center mb-4">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center mr-3 ${
              validation.overall.isValid 
                ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400' 
                : 'bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400'
            }`}>
              {validation.overall.isValid ? (
                <CheckCircle className="w-5 h-5" />
              ) : (
                <AlertCircle className="w-5 h-5" />
              )}
            </div>
            <p className={`text-lg font-semibold ${
              validation.overall.isValid ? 'text-emerald-900 dark:text-emerald-100' : 'text-amber-900 dark:text-amber-100'
            }`}>
              {validation.overall.isValid ? 'Configuration Valid' : 'Configuration Issues'}
            </p>
          </div>
          <p className={`text-sm mb-4 ${
            validation.overall.isValid ? 'text-emerald-800 dark:text-emerald-200' : 'text-amber-800 dark:text-amber-200'
          }`}>
            {validation.overall.message}
          </p>
          
          {(config.initialCapital && config.startDate && config.endDate) && (
            <div className="pt-4 border-t border-current">
              <p className="text-sm font-semibold mb-3">Configuration Summary:</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Initial Capital:</span>
                  <span className="font-medium">{config.initialCapital?.toLocaleString()} {config.shareClass}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Backtest Period:</span>
                  <span className="font-medium">{config.startDate} to {config.endDate}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600 dark:text-slate-400">Strategy Mode:</span>
                  <span className="font-medium">{config.mode}</span>
                </div>
              </div>
            </div>
          )}
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
              disabled={!validation.overall.isValid}
              className={`
                px-8 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center gap-2
                ${validation.overall.isValid
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg hover:shadow-xl transform hover:-translate-y-0.5'
                  : 'bg-slate-300 dark:bg-slate-700 text-slate-500 dark:text-slate-400 cursor-not-allowed'
                }
              `}
            >
              Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}