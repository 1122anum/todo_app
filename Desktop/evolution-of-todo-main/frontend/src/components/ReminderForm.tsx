/**
 * ReminderForm component for creating and managing task reminders.
 *
 * Allows users to set reminder times for tasks.
 */
import React, { useState } from 'react';
import styles from './ReminderForm.module.css';

export interface ReminderData {
  scheduled_time: string;  // ISO 8601
  notification_channel: 'in_app';
}

interface ReminderFormProps {
  taskId: number;
  taskTitle: string;
  dueDate?: string;  // ISO 8601
  onSubmit: (reminder: ReminderData) => void;
  onCancel: () => void;
}

export const ReminderForm: React.FC<ReminderFormProps> = ({
  taskId,
  taskTitle,
  dueDate,
  onSubmit,
  onCancel,
}) => {
  const [reminderType, setReminderType] = useState<'custom' | 'before-due'>('before-due');
  const [customDate, setCustomDate] = useState<string>('');
  const [customTime, setCustomTime] = useState<string>('09:00');
  const [minutesBefore, setMinutesBefore] = useState<number>(60);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    let scheduledTime: Date;

    if (reminderType === 'custom') {
      // Custom date and time
      if (!customDate) {
        alert('Please select a date');
        return;
      }
      scheduledTime = new Date(`${customDate}T${customTime}`);
    } else {
      // Before due date
      if (!dueDate) {
        alert('Task must have a due date to set reminder before due');
        return;
      }
      const dueDateTime = new Date(dueDate);
      scheduledTime = new Date(dueDateTime.getTime() - minutesBefore * 60 * 1000);
    }

    // Validate scheduled time is in the future
    if (scheduledTime <= new Date()) {
      alert('Reminder time must be in the future');
      return;
    }

    const reminder: ReminderData = {
      scheduled_time: scheduledTime.toISOString(),
      notification_channel: 'in_app',
    };

    onSubmit(reminder);
  };

  const getMinDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  const getMaxDate = () => {
    if (dueDate) {
      return new Date(dueDate).toISOString().split('T')[0];
    }
    return undefined;
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <h3 className={styles.title}>Set Reminder</h3>
      <p className={styles.taskTitle}>{taskTitle}</p>

      {/* Reminder Type Selection */}
      <div className={styles.field}>
        <label className={styles.label}>Remind me</label>
        <div className={styles.typeButtons}>
          {dueDate && (
            <button
              type="button"
              className={`${styles.typeButton} ${
                reminderType === 'before-due' ? styles.active : ''
              }`}
              onClick={() => setReminderType('before-due')}
            >
              Before Due Date
            </button>
          )}
          <button
            type="button"
            className={`${styles.typeButton} ${
              reminderType === 'custom' ? styles.active : ''
            }`}
            onClick={() => setReminderType('custom')}
          >
            Custom Time
          </button>
        </div>
      </div>

      {/* Before Due Date Options */}
      {reminderType === 'before-due' && dueDate && (
        <div className={styles.field}>
          <label className={styles.label}>
            <select
              value={minutesBefore}
              onChange={(e) => setMinutesBefore(parseInt(e.target.value))}
              className={styles.select}
            >
              <option value={15}>15 minutes before</option>
              <option value={30}>30 minutes before</option>
              <option value={60}>1 hour before</option>
              <option value={120}>2 hours before</option>
              <option value={1440}>1 day before</option>
              <option value={2880}>2 days before</option>
              <option value={10080}>1 week before</option>
            </select>
          </label>
          <p className={styles.hint}>
            Due: {new Date(dueDate).toLocaleString()}
          </p>
        </div>
      )}

      {/* Custom Date and Time */}
      {reminderType === 'custom' && (
        <>
          <div className={styles.field}>
            <label className={styles.label}>
              Date
              <input
                type="date"
                value={customDate}
                onChange={(e) => setCustomDate(e.target.value)}
                min={getMinDate()}
                max={getMaxDate()}
                className={styles.dateInput}
                required
              />
            </label>
          </div>
          <div className={styles.field}>
            <label className={styles.label}>
              Time
              <input
                type="time"
                value={customTime}
                onChange={(e) => setCustomTime(e.target.value)}
                className={styles.timeInput}
                required
              />
            </label>
          </div>
        </>
      )}

      {/* Notification Channel (read-only for Phase V) */}
      <div className={styles.field}>
        <label className={styles.label}>
          Notification
          <input
            type="text"
            value="In-app notification"
            className={styles.channelInput}
            disabled
          />
        </label>
        <p className={styles.hint}>
          Email and push notifications coming soon
        </p>
      </div>

      {/* Summary */}
      <div className={styles.summary}>
        <strong>Summary:</strong>{' '}
        {reminderType === 'before-due' && dueDate ? (
          <>
            Remind {minutesBefore >= 1440 ? `${minutesBefore / 1440} day(s)` : minutesBefore >= 60 ? `${minutesBefore / 60} hour(s)` : `${minutesBefore} minute(s)`} before due date
          </>
        ) : (
          <>
            Remind on {customDate ? new Date(`${customDate}T${customTime}`).toLocaleString() : 'selected date'}
          </>
        )}
      </div>

      {/* Actions */}
      <div className={styles.actions}>
        <button type="button" onClick={onCancel} className={styles.cancelButton}>
          Cancel
        </button>
        <button type="submit" className={styles.submitButton}>
          Set Reminder
        </button>
      </div>
    </form>
  );
};

/**
 * ReminderList component for displaying task reminders.
 */
interface ReminderListProps {
  reminders: Array<{
    id: number;
    scheduled_time: string;
    status: string;
    snoozed_until?: string;
  }>;
  onSnooze: (reminderId: number, minutes: number) => void;
  onDelete: (reminderId: number) => void;
}

export const ReminderList: React.FC<ReminderListProps> = ({
  reminders,
  onSnooze,
  onDelete,
}) => {
  if (reminders.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No reminders set</p>
      </div>
    );
  }

  return (
    <div className={styles.reminderList}>
      {reminders.map((reminder) => (
        <div key={reminder.id} className={styles.reminderItem}>
          <div className={styles.reminderInfo}>
            <span className={styles.reminderTime}>
              {new Date(reminder.scheduled_time).toLocaleString()}
            </span>
            <span className={`${styles.reminderStatus} ${styles[reminder.status]}`}>
              {reminder.status}
            </span>
          </div>
          <div className={styles.reminderActions}>
            {reminder.status === 'pending' && (
              <>
                <button
                  onClick={() => onSnooze(reminder.id, 10)}
                  className={styles.snoozeButton}
                  title="Snooze 10 minutes"
                >
                  Snooze
                </button>
                <button
                  onClick={() => onDelete(reminder.id)}
                  className={styles.deleteButton}
                  title="Delete reminder"
                >
                  Delete
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
