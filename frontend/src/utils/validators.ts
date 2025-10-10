// Utility functions for validation

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePassword = (password: string): { valid: boolean; message?: string } => {
  if (password.length < 8) {
    return { valid: false, message: 'Password must be at least 8 characters long' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter' };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one lowercase letter' };
  }
  if (!/\d/.test(password)) {
    return { valid: false, message: 'Password must contain at least one number' };
  }
  return { valid: true };
};

export const validateCapitalAmount = (amount: number, min: number = 100, max: number = 1000000): { valid: boolean; message?: string } => {
  if (amount < min) {
    return { valid: false, message: `Minimum capital amount is $${min.toLocaleString()}` };
  }
  if (amount > max) {
    return { valid: false, message: `Maximum capital amount is $${max.toLocaleString()}` };
  }
  return { valid: true };
};

export const validateDateRange = (startDate: string, endDate: string): { valid: boolean; message?: string } => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const now = new Date();
  
  if (start >= end) {
    return { valid: false, message: 'End date must be after start date' };
  }
  
  if (start >= now) {
    return { valid: false, message: 'Start date must be in the past' };
  }
  
  const daysDiff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (daysDiff > 365) {
    return { valid: false, message: 'Date range cannot exceed 1 year' };
  }
  
  return { valid: true };
};

export const validateRequired = (value: any, fieldName: string): { valid: boolean; message?: string } => {
  if (value === null || value === undefined || value === '') {
    return { valid: false, message: `${fieldName} is required` };
  }
  return { valid: true };
};

export const validateUsername = (username: string): { valid: boolean; message?: string } => {
  if (username.length < 3) {
    return { valid: false, message: 'Username must be at least 3 characters long' };
  }
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return { valid: false, message: 'Username can only contain letters, numbers, and underscores' };
  }
  return { valid: true };
};

export const validateStrategyName = (strategyName: string): { valid: boolean; message?: string } => {
  const validStrategies = [
    'usdt_market_neutral',
    'btc_basis',
    'eth_basis',
    'eth_leveraged',
    'pure_lending',
    'eth_staking_only',
    'usdt_market_neutral_no_leverage'
  ];
  
  if (!validStrategies.includes(strategyName)) {
    return { valid: false, message: `Invalid strategy name. Must be one of: ${validStrategies.join(', ')}` };
  }
  return { valid: true };
};

export const validateShareClass = (shareClass: string): { valid: boolean; message?: string } => {
  if (!['usdt', 'eth'].includes(shareClass.toLowerCase())) {
    return { valid: false, message: 'Share class must be either USDT or ETH' };
  }
  return { valid: true };
};
