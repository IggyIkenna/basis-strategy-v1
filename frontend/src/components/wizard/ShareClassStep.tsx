import React from 'react';
import { Check } from 'lucide-react';

interface ShareClassStepProps {
  selectedClass: 'USDT' | 'ETH';
  onSelect: (shareClass: 'USDT' | 'ETH') => void;
}

export function ShareClassStep({ selectedClass, onSelect }: ShareClassStepProps) {
  const shareClasses = [
    {
      id: 'USDT' as const,
      name: 'USDT Share Class',
      description: 'Trade with USDT as the base currency',
      features: [
        'Stable value reference',
        'Lower volatility',
        'Suitable for conservative strategies'
      ],
      icon: '💵'
    },
    {
      id: 'ETH' as const,
      name: 'ETH Share Class',
      description: 'Trade with ETH as the base currency',
      features: [
        'Higher potential returns',
        'ETH price exposure',
        'Suitable for aggressive strategies'
      ],
      icon: '⚡'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Choose Your Share Class
        </h2>
        <p className="text-gray-600">
          Select the base currency for your trading strategy
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {shareClasses.map((shareClass) => (
          <div
            key={shareClass.id}
            onClick={() => onSelect(shareClass.id)}
            className={`relative p-6 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
              selectedClass === shareClass.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            {selectedClass === shareClass.id && (
              <div className="absolute top-4 right-4">
                <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                  <Check className="w-4 h-4 text-white" />
                </div>
              </div>
            )}

            <div className="flex items-center mb-4">
              <span className="text-3xl mr-3">{shareClass.icon}</span>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {shareClass.name}
                </h3>
                <p className="text-sm text-gray-600">
                  {shareClass.description}
                </p>
              </div>
            </div>

            <ul className="space-y-2">
              {shareClass.features.map((feature, index) => (
                <li key={index} className="flex items-center text-sm text-gray-600">
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-2" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {selectedClass && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Selected:</strong> {shareClasses.find(sc => sc.id === selectedClass)?.name}
          </p>
          <p className="text-sm text-blue-700 mt-1">
            This choice will affect the available strategy modes and risk parameters.
          </p>
        </div>
      )}
    </div>
  );
}