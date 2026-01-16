// src/utils/statusHelpers.js
import {
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
} from 'lucide-react';

/**
 * Get icon component for warranty status
 * @param {string} status - Warranty status (case-insensitive)
 * @returns {JSX.Element} Icon component
 */
export const getWarrantyStatusIcon = (status) => {
  const normalizedStatus = status?.toLowerCase();
  switch (normalizedStatus) {
    case 'active':
      return <CheckCircle2 className="w-4 h-4" />;
    case 'expired':
      return <Clock className="w-4 h-4" />;
    case 'void':
      return <XCircle className="w-4 h-4" />;
    default:
      return <AlertCircle className="w-4 h-4" />;
  }
};

/**
 * Get color classes for warranty status badge
 * @param {string} status - Warranty status (case-insensitive)
 * @returns {string} Tailwind CSS classes
 */
export const getWarrantyStatusColor = (status) => {
  const normalizedStatus = status?.toLowerCase();
  const colors = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    expired: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    void: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  };
  return colors[normalizedStatus] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
};

/**
 * Get color classes for warranty claim status badge
 * @param {string} status - Claim status (case-insensitive)
 * @returns {string} Tailwind CSS classes
 */
export const getClaimStatusColor = (status) => {
  const normalizedStatus = status?.toLowerCase();
  const colors = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    approved: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    in_progress: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
    resolved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  };
  return colors[normalizedStatus] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
};

/**
 * Get color for warranty expiration display
 * @param {number} daysRemaining - Days remaining until expiration
 * @returns {string} Tailwind CSS color classes
 */
export const getExpirationColor = (daysRemaining) => {
  if (daysRemaining === null || daysRemaining < 0) {
    return 'text-gray-500 dark:text-gray-400';
  }
  if (daysRemaining <= 30) {
    return 'text-red-600 dark:text-red-400 font-semibold';
  }
  if (daysRemaining <= 90) {
    return 'text-yellow-600 dark:text-yellow-400';
  }
  return 'text-green-600 dark:text-green-400';
};

/**
 * Format days remaining display text
 * @param {number} daysRemaining - Days remaining until expiration
 * @returns {string} Formatted text
 */
export const formatDaysRemaining = (daysRemaining) => {
  if (daysRemaining === null) {
    return 'N/A';
  }
  if (daysRemaining < 0) {
    return 'Expired';
  }
  if (daysRemaining === 0) {
    return 'Expires today';
  }
  if (daysRemaining === 1) {
    return '1 day';
  }
  return `${daysRemaining} days`;
};
