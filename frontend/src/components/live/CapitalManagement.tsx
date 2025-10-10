// Capital management component for deposits and withdrawals

import React, { useState } from 'react';
import { apiClient } from '../../services/api';
import { DepositRequest, WithdrawRequest } from '../../types';
import { validateCapitalAmount } from '../../utils/validators';
import { formatCurrency } from '../../utils/formatters';
import { VALIDATION_LIMITS } from '../../utils/constants';

interface CapitalManagementProps {
  className?: string;
}

export const CapitalManagement: React.FC<CapitalManagementProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState<'deposit' | 'withdraw'>('deposit');
  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [depositCurrency, setDepositCurrency] = useState('USDT');
  const [withdrawCurrency, setWithdrawCurrency] = useState('USDT');
  const [depositShareClass, setDepositShareClass] = useState('usdt');
  const [withdrawShareClass, setWithdrawShareClass] = useState('usdt');
  const [withdrawalType, setWithdrawalType] = useState<'fast' | 'slow'>('fast');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showDepositConfirm, setShowDepositConfirm] = useState(false);
  const [showWithdrawConfirm, setShowWithdrawConfirm] = useState(false);

  const handleDeposit = async () => {
    const amount = parseFloat(depositAmount);
    
    // Validate amount
    const validation = validateCapitalAmount(amount, VALIDATION_LIMITS.MIN_CAPITAL, VALIDATION_LIMITS.MAX_CAPITAL);
    if (!validation.valid) {
      setError(validation.message || 'Invalid deposit amount');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const request: DepositRequest = {
        amount,
        currency: depositCurrency,
        share_class: depositShareClass,
        source: 'manual'
      };

      const response = await apiClient.depositCapital(request);
      
      setSuccess(`Deposit of ${formatCurrency(amount)} ${depositCurrency} queued successfully`);
      setDepositAmount('');
      setShowDepositConfirm(false);
    } catch (err: any) {
      setError(err.message || 'Failed to process deposit');
    } finally {
      setLoading(false);
    }
  };

  const handleWithdraw = async () => {
    const amount = parseFloat(withdrawAmount);
    
    // Validate amount
    const validation = validateCapitalAmount(amount, VALIDATION_LIMITS.MIN_CAPITAL, VALIDATION_LIMITS.MAX_CAPITAL);
    if (!validation.valid) {
      setError(validation.message || 'Invalid withdrawal amount');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const request: WithdrawRequest = {
        amount,
        currency: withdrawCurrency,
        share_class: withdrawShareClass,
        withdrawal_type: withdrawalType
      };

      const response = await apiClient.withdrawCapital(request);
      
      setSuccess(`Withdrawal of ${formatCurrency(amount)} ${withdrawCurrency} queued successfully`);
      setWithdrawAmount('');
      setShowWithdrawConfirm(false);
    } catch (err: any) {
      setError(err.message || 'Failed to process withdrawal');
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Capital Management</h3>
        <p className="text-sm text-gray-500">Deposit and withdraw capital from the strategy</p>
      </div>

      <div className="p-6">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => { setActiveTab('deposit'); clearMessages(); }}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'deposit'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Deposit
            </button>
            <button
              onClick={() => { setActiveTab('withdraw'); clearMessages(); }}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'withdraw'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Withdraw
            </button>
          </nav>
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-4 rounded-md bg-green-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Success</h3>
                <div className="mt-2 text-sm text-green-700">{success}</div>
              </div>
            </div>
          </div>
        )}

        {/* Deposit Form */}
        {activeTab === 'deposit' && (
          <div className="space-y-4">
            <div>
              <label htmlFor="deposit-amount" className="block text-sm font-medium text-gray-700">
                Amount
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span className="text-gray-500 sm:text-sm">$</span>
                </div>
                <input
                  type="number"
                  id="deposit-amount"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-7 pr-12 sm:text-sm border-gray-300 rounded-md"
                  placeholder="0.00"
                  min={VALIDATION_LIMITS.MIN_CAPITAL}
                  max={VALIDATION_LIMITS.MAX_CAPITAL}
                  step="0.01"
                />
                <div className="absolute inset-y-0 right-0 flex items-center">
                  <select
                    value={depositCurrency}
                    onChange={(e) => setDepositCurrency(e.target.value)}
                    className="focus:ring-blue-500 focus:border-blue-500 h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md"
                  >
                    <option value="USDT">USDT</option>
                    <option value="ETH">ETH</option>
                  </select>
                </div>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Minimum: ${VALIDATION_LIMITS.MIN_CAPITAL.toLocaleString()}, Maximum: ${VALIDATION_LIMITS.MAX_CAPITAL.toLocaleString()}
              </p>
            </div>

            <div>
              <label htmlFor="deposit-share-class" className="block text-sm font-medium text-gray-700">
                Share Class
              </label>
              <select
                id="deposit-share-class"
                value={depositShareClass}
                onChange={(e) => setDepositShareClass(e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="usdt">USDT</option>
                <option value="eth">ETH</option>
              </select>
            </div>

            <button
              onClick={() => setShowDepositConfirm(true)}
              disabled={loading || !depositAmount}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Deposit Capital'}
            </button>
          </div>
        )}

        {/* Withdraw Form */}
        {activeTab === 'withdraw' && (
          <div className="space-y-4">
            <div>
              <label htmlFor="withdraw-amount" className="block text-sm font-medium text-gray-700">
                Amount
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span className="text-gray-500 sm:text-sm">$</span>
                </div>
                <input
                  type="number"
                  id="withdraw-amount"
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-7 pr-12 sm:text-sm border-gray-300 rounded-md"
                  placeholder="0.00"
                  min={VALIDATION_LIMITS.MIN_CAPITAL}
                  max={VALIDATION_LIMITS.MAX_CAPITAL}
                  step="0.01"
                />
                <div className="absolute inset-y-0 right-0 flex items-center">
                  <select
                    value={withdrawCurrency}
                    onChange={(e) => setWithdrawCurrency(e.target.value)}
                    className="focus:ring-blue-500 focus:border-blue-500 h-full py-0 pl-2 pr-7 border-transparent bg-transparent text-gray-500 sm:text-sm rounded-md"
                  >
                    <option value="USDT">USDT</option>
                    <option value="ETH">ETH</option>
                  </select>
                </div>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Minimum: ${VALIDATION_LIMITS.MIN_CAPITAL.toLocaleString()}, Maximum: ${VALIDATION_LIMITS.MAX_CAPITAL.toLocaleString()}
              </p>
            </div>

            <div>
              <label htmlFor="withdraw-share-class" className="block text-sm font-medium text-gray-700">
                Share Class
              </label>
              <select
                id="withdraw-share-class"
                value={withdrawShareClass}
                onChange={(e) => setWithdrawShareClass(e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="usdt">USDT</option>
                <option value="eth">ETH</option>
              </select>
            </div>

            <div>
              <label htmlFor="withdrawal-type" className="block text-sm font-medium text-gray-700">
                Withdrawal Type
              </label>
              <select
                id="withdrawal-type"
                value={withdrawalType}
                onChange={(e) => setWithdrawalType(e.target.value as 'fast' | 'slow')}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="fast">Fast (from available reserves)</option>
                <option value="slow">Slow (unwind positions)</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                {withdrawalType === 'fast' 
                  ? 'Immediate withdrawal from available reserves'
                  : 'May take time as positions need to be unwound'
                }
              </p>
            </div>

            <button
              onClick={() => setShowWithdrawConfirm(true)}
              disabled={loading || !withdrawAmount}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Withdraw Capital'}
            </button>
          </div>
        )}
      </div>

      {/* Deposit Confirmation Dialog */}
      {showDepositConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">Confirm Deposit</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to deposit <strong>{formatCurrency(parseFloat(depositAmount))} {depositCurrency}</strong> to the <strong>{depositShareClass.toUpperCase()}</strong> share class?
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleDeposit}
                  className="px-4 py-2 bg-green-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-300"
                >
                  Deposit
                </button>
                <button
                  onClick={() => setShowDepositConfirm(false)}
                  className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Withdraw Confirmation Dialog */}
      {showWithdrawConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">Confirm Withdrawal</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500">
                  Are you sure you want to withdraw <strong>{formatCurrency(parseFloat(withdrawAmount))} {withdrawCurrency}</strong> from the <strong>{withdrawShareClass.toUpperCase()}</strong> share class?
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  Withdrawal type: <strong>{withdrawalType}</strong>
                </p>
              </div>
              <div className="items-center px-4 py-3">
                <button
                  onClick={handleWithdraw}
                  className="px-4 py-2 bg-red-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-300"
                >
                  Withdraw
                </button>
                <button
                  onClick={() => setShowWithdrawConfirm(false)}
                  className="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

