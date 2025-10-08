import React, { useState, useEffect } from 'react';
import { DollarSign, Calendar, Info, CheckCircle, AlertCircle } from 'lucide-react';

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
}

export function BasicConfigStep({ config, onUpdate }: BasicConfigStepProps) {
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
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Basic Configuration
        </h2>
        <p className="text-gray-600">
          Set your initial capital and backtest period
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Initial Capital */}
        <div className="space-y-4">
          <div className="flex items-center">
            <DollarSign className="w-5 h-5 text-gray-500 mr-2" />
            <label className="text-sm font-medium text-gray-700">
              Initial Capital ({config.shareClass})
            </label>
          </div>
          
          <div className="space-y-3">
            <div className="relative">
              <input
                type="number"
                value={config.initialCapital || ''}
                onChange={(e) => handleCapitalChange(e.target.value)}
                placeholder={`Enter amount in ${config.shareClass}`}
                className={`w-full px-3 py-2 pr-10 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  validation.capital.isValid 
                    ? 'border-green-300 bg-green-50' 
                    : config.initialCapital 
                      ? 'border-red-300 bg-red-50' 
                      : 'border-gray-300'
                }`}
                min="0"
                step="0.01"
              />
              {config.initialCapital && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  {validation.capital.isValid ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  )}
                </div>
              )}
            </div>
            {config.initialCapital && (
              <p className={`text-xs mt-1 ${
                validation.capital.isValid ? 'text-green-600' : 'text-red-600'
              }`}>
                {validation.capital.message}
              </p>
            )}
            
            <div className="grid grid-cols-2 gap-2">
              {getCapitalSuggestions().map((amount) => (
                <button
                  key={amount}
                  onClick={() => onUpdate({ initialCapital: amount })}
                  className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                    config.initialCapital === amount
                      ? 'bg-blue-50 border-blue-500 text-blue-700'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {amount.toLocaleString()} {config.shareClass}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Date Range */}
        <div className="space-y-4">
          <div className="flex items-center">
            <Calendar className="w-5 h-5 text-gray-500 mr-2" />
            <label className="text-sm font-medium text-gray-700">
              Backtest Period
            </label>
          </div>
          
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Start Date</label>
              <div className="relative">
                <input
                  type="date"
                  value={config.startDate || ''}
                  onChange={(e) => handleDateChange('startDate', e.target.value)}
                  min={getMinDate()}
                  max={getMaxDate()}
                  className={`w-full px-3 py-2 pr-10 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    validation.startDate.isValid 
                      ? 'border-green-300 bg-green-50' 
                      : config.startDate 
                        ? 'border-red-300 bg-red-50' 
                        : 'border-gray-300'
                  }`}
                />
                {config.startDate && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    {validation.startDate.isValid ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                )}
              </div>
              {config.startDate && (
                <p className={`text-xs mt-1 ${
                  validation.startDate.isValid ? 'text-green-600' : 'text-red-600'
                }`}>
                  {validation.startDate.message}
                </p>
              )}
            </div>
            
            <div>
              <label className="block text-xs text-gray-600 mb-1">End Date</label>
              <div className="relative">
                <input
                  type="date"
                  value={config.endDate || ''}
                  onChange={(e) => handleDateChange('endDate', e.target.value)}
                  min={config.startDate || getMinDate()}
                  max={getMaxDate()}
                  className={`w-full px-3 py-2 pr-10 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    validation.endDate.isValid 
                      ? 'border-green-300 bg-green-50' 
                      : config.endDate 
                        ? 'border-red-300 bg-red-50' 
                        : 'border-gray-300'
                  }`}
                />
                {config.endDate && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    {validation.endDate.isValid ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                )}
              </div>
              {config.endDate && (
                <p className={`text-xs mt-1 ${
                  validation.endDate.isValid ? 'text-green-600' : 'text-red-600'
                }`}>
                  {validation.endDate.message}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Info Panel */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <Info className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Configuration Notes:</p>
            <ul className="space-y-1 text-blue-700">
              <li>• Capital amount determines your position sizes and risk exposure</li>
              <li>• Backtest period should be at least 30 days for meaningful results</li>
              <li>• Historical data availability may limit your date range</li>
              <li>• Strategy performance can vary significantly across different time periods</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Validation Summary */}
      <div className={`mt-6 p-4 border rounded-lg ${
        validation.overall.isValid 
          ? 'bg-green-50 border-green-200' 
          : 'bg-yellow-50 border-yellow-200'
      }`}>
        <div className="flex items-center mb-2">
          {validation.overall.isValid ? (
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
          ) : (
            <AlertCircle className="w-5 h-5 text-yellow-600 mr-2" />
          )}
          <p className={`text-sm font-medium ${
            validation.overall.isValid ? 'text-green-800' : 'text-yellow-800'
          }`}>
            {validation.overall.isValid ? 'Configuration Valid' : 'Configuration Issues'}
          </p>
        </div>
        <p className={`text-sm ${
          validation.overall.isValid ? 'text-green-700' : 'text-yellow-700'
        }`}>
          {validation.overall.message}
        </p>
        
        {(config.initialCapital && config.startDate && config.endDate) && (
          <div className="mt-3 pt-3 border-t border-current">
            <p className="text-sm font-medium mb-2">Configuration Summary:</p>
            <ul className="text-sm space-y-1">
              <li>• Initial Capital: {config.initialCapital?.toLocaleString()} {config.shareClass}</li>
              <li>• Backtest Period: {config.startDate} to {config.endDate}</li>
              <li>• Strategy Mode: {config.mode}</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}