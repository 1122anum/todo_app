/**
 * RecurringTaskForm component for creating recurring tasks.
 *
 * Allows users to configure recurrence patterns (daily, weekly, monthly).
 */
import React, { useState } from 'react';
import styles from './RecurringTaskForm.module.css';

export interface RecurrencePattern {
  frequency: 'daily' | 'weekly' | 'monthly';
  interval: number;
  daysOfWeek?: number[];  // 0=Sunday, 6=Saturday
  dayOfMonth?: number;    // 1-31
  startDate: string;      // ISO 8601
  endDate?: string;       // ISO 8601 (optional)
}

interface RecurringTaskFormProps {
  onSubmit: (pattern: RecurrencePattern) => void;
  onCancel: () => void;
  initialPattern?: RecurrencePattern;
}

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sun' },
  { value: 1, label: 'Mon' },
  { value: 2, label: 'Tue' },
  { value: 3, label: 'Wed' },
  { value: 4, label: 'Thu' },
  { value: 5, label: 'Fri' },
  { value: 6, label: 'Sat' },
];

export const RecurringTaskForm: React.FC<RecurringTaskFormProps> = ({
  onSubmit,
  onCancel,
  initialPattern,
}) => {
  const [frequency, setFrequency] = useState<'daily' | 'weekly' | 'monthly'>(
    initialPattern?.frequency || 'daily'
  );
  const [interval, setInterval] = useState<number>(initialPattern?.interval || 1);
  const [daysOfWeek, setDaysOfWeek] = useState<number[]>(
    initialPattern?.daysOfWeek || []
  );
  const [dayOfMonth, setDayOfMonth] = useState<number>(
    initialPattern?.dayOfMonth || 1
  );
  const [startDate, setStartDate] = useState<string>(
    initialPattern?.startDate || new Date().toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState<string>(initialPattern?.endDate || '');
  const [hasEndDate, setHasEndDate] = useState<boolean>(!!initialPattern?.endDate);

  const handleDayOfWeekToggle = (day: number) => {
    setDaysOfWeek((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort()
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (frequency === 'weekly' && daysOfWeek.length === 0) {
      alert('Please select at least one day of the week');
      return;
    }

    if (interval < 1) {
      alert('Interval must be at least 1');
      return;
    }

    const pattern: RecurrencePattern = {
      frequency,
      interval,
      startDate: new Date(startDate).toISOString(),
      ...(frequency === 'weekly' && { daysOfWeek }),
      ...(frequency === 'monthly' && { dayOfMonth }),
      ...(hasEndDate && endDate && { endDate: new Date(endDate).toISOString() }),
    };

    onSubmit(pattern);
  };

  const getFrequencyLabel = () => {
    if (interval === 1) {
      return frequency === 'daily' ? 'day' : frequency === 'weekly' ? 'week' : 'month';
    }
    return frequency === 'daily' ? 'days' : frequency === 'weekly' ? 'weeks' : 'months';
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <h3 className={styles.title}>Recurring Task Pattern</h3>

      {/* Frequency Selection */}
      <div className={styles.field}>
        <label className={styles.label}>Repeat</label>
        <div className={styles.frequencyButtons}>
          <button
            type="button"
            className={`${styles.frequencyButton} ${
              frequency === 'daily' ? styles.active : ''
            }`}
            onClick={() => setFrequency('daily')}
          >
            Daily
          </button>
          <button
            type="button"
            className={`${styles.frequencyButton} ${
              frequency === 'weekly' ? styles.active : ''
            }`}
            onClick={() => setFrequency('weekly')}
          >
            Weekly
          </button>
          <button
            type="button"
            className={`${styles.frequencyButton} ${
              frequency === 'monthly' ? styles.active : ''
            }`}
            onClick={() => setFrequency('monthly')}
          >
            Monthly
          </button>
        </div>
      </div>

      {/* Interval */}
      <div className={styles.field}>
        <label className={styles.label}>
          Every
          <input
            type="number"
            min="1"
            max="365"
            value={interval}
            onChange={(e) => setInterval(parseInt(e.target.value) || 1)}
            className={styles.intervalInput}
          />
          {getFrequencyLabel()}
        </label>
      </div>

      {/* Days of Week (for weekly) */}
      {frequency === 'weekly' && (
        <div className={styles.field}>
          <label className={styles.label}>On days</label>
          <div className={styles.daysOfWeek}>
            {DAYS_OF_WEEK.map((day) => (
              <button
                key={day.value}
                type="button"
                className={`${styles.dayButton} ${
                  daysOfWeek.includes(day.value) ? styles.active : ''
                }`}
                onClick={() => handleDayOfWeekToggle(day.value)}
              >
                {day.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Day of Month (for monthly) */}
      {frequency === 'monthly' && (
        <div className={styles.field}>
          <label className={styles.label}>
            On day
            <input
              type="number"
              min="1"
              max="31"
              value={dayOfMonth}
              onChange={(e) => setDayOfMonth(parseInt(e.target.value) || 1)}
              className={styles.dayOfMonthInput}
            />
            of the month
          </label>
        </div>
      )}

      {/* Start Date */}
      <div className={styles.field}>
        <label className={styles.label}>
          Start date
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className={styles.dateInput}
            required
          />
        </label>
      </div>

      {/* End Date */}
      <div className={styles.field}>
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={hasEndDate}
            onChange={(e) => setHasEndDate(e.target.checked)}
            className={styles.checkbox}
          />
          Set end date
        </label>
        {hasEndDate && (
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className={styles.dateInput}
            min={startDate}
          />
        )}
      </div>

      {/* Summary */}
      <div className={styles.summary}>
        <strong>Summary:</strong> Repeats every {interval} {getFrequencyLabel()}
        {frequency === 'weekly' && daysOfWeek.length > 0 && (
          <> on {daysOfWeek.map((d) => DAYS_OF_WEEK[d].label).join(', ')}</>
        )}
        {frequency === 'monthly' && <> on day {dayOfMonth}</>}, starting{' '}
        {new Date(startDate).toLocaleDateString()}
        {hasEndDate && endDate && (
          <> until {new Date(endDate).toLocaleDateString()}</>
        )}
      </div>

      {/* Actions */}
      <div className={styles.actions}>
        <button type="button" onClick={onCancel} className={styles.cancelButton}>
          Cancel
        </button>
        <button type="submit" className={styles.submitButton}>
          Save Pattern
        </button>
      </div>
    </form>
  );
};
