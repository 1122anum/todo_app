/**
 * PrioritySelector component for selecting task priority.
 *
 * Displays priority options with color coding.
 */
import React from 'react';
import styles from './PrioritySelector.module.css';

export type Priority = 'high' | 'medium' | 'low';

interface PrioritySelectorProps {
  value: Priority;
  onChange: (priority: Priority) => void;
  disabled?: boolean;
}

const PRIORITY_OPTIONS: Array<{
  value: Priority;
  label: string;
  color: string;
  icon: string;
}> = [
  { value: 'high', label: 'High', color: '#ef4444', icon: '🔴' },
  { value: 'medium', label: 'Medium', color: '#f59e0b', icon: '🟡' },
  { value: 'low', label: 'Low', color: '#10b981', icon: '🟢' },
];

export const PrioritySelector: React.FC<PrioritySelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  return (
    <div className={styles.container}>
      <label className={styles.label}>Priority</label>
      <div className={styles.options}>
        {PRIORITY_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`${styles.option} ${
              value === option.value ? styles.active : ''
            }`}
            style={{
              borderColor: value === option.value ? option.color : undefined,
              backgroundColor: value === option.value ? `${option.color}15` : undefined,
            }}
            onClick={() => onChange(option.value)}
            disabled={disabled}
            aria-label={`Set priority to ${option.label}`}
          >
            <span className={styles.icon}>{option.icon}</span>
            <span className={styles.optionLabel}>{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

/**
 * PriorityBadge component for displaying task priority.
 */
interface PriorityBadgeProps {
  priority: Priority;
  size?: 'small' | 'medium' | 'large';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({
  priority,
  size = 'medium',
}) => {
  const option = PRIORITY_OPTIONS.find((opt) => opt.value === priority);

  if (!option) {
    return null;
  }

  return (
    <span
      className={`${styles.badge} ${styles[size]}`}
      style={{
        backgroundColor: `${option.color}15`,
        color: option.color,
        borderColor: option.color,
      }}
      title={`Priority: ${option.label}`}
    >
      <span className={styles.badgeIcon}>{option.icon}</span>
      <span className={styles.badgeLabel}>{option.label}</span>
    </span>
  );
};

/**
 * Get priority color for styling.
 */
export const getPriorityColor = (priority: Priority): string => {
  const option = PRIORITY_OPTIONS.find((opt) => opt.value === priority);
  return option?.color || '#6b7280';
};
