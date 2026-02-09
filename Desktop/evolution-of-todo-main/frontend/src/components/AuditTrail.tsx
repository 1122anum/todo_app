/**
 * AuditTrail component for displaying task change history.
 *
 * Features:
 * - Display chronological list of task changes
 * - Show event type, timestamp, and changes
 * - Expandable change details
 * - Filter by event type
 * - Pagination support
 */
import React, { useState, useEffect } from 'react';
import styles from './AuditTrail.module.css';

export interface AuditRecord {
  audit_id: string;
  event_type: 'task.created' | 'task.updated' | 'task.completed' | 'task.deleted';
  timestamp: string;
  task_id: number;
  task_title: string;
  changes?: Record<string, { old_value: any; new_value: any }>;
  source: string;
  correlation_id: string;
}

interface AuditTrailProps {
  userId: number;
  taskId?: number;
  limit?: number;
}

export const AuditTrail: React.FC<AuditTrailProps> = ({
  userId,
  taskId,
  limit = 50,
}) => {
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [expandedRecords, setExpandedRecords] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchAuditTrail();
  }, [userId, taskId, filter]);

  const fetchAuditTrail = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const params = new URLSearchParams({
        limit: limit.toString(),
      });

      if (filter !== 'all') {
        params.append('event_type', filter);
      }

      const endpoint = taskId
        ? `/api/audit/users/${userId}/tasks/${taskId}?${params}`
        : `/api/audit/users/${userId}/tasks?${params}`;

      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch audit trail');
      }

      const data: AuditRecord[] = await response.json();
      setRecords(data);
    } catch (err) {
      console.error('Failed to fetch audit trail:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch audit trail');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleExpanded = (auditId: string) => {
    setExpandedRecords(prev => {
      const next = new Set(prev);
      if (next.has(auditId)) {
        next.delete(auditId);
      } else {
        next.add(auditId);
      }
      return next;
    });
  };

  const getEventIcon = (eventType: string): string => {
    switch (eventType) {
      case 'task.created':
        return '➕';
      case 'task.updated':
        return '✏️';
      case 'task.completed':
        return '✅';
      case 'task.deleted':
        return '🗑️';
      default:
        return '📝';
    }
  };

  const getEventLabel = (eventType: string): string => {
    switch (eventType) {
      case 'task.created':
        return 'Created';
      case 'task.updated':
        return 'Updated';
      case 'task.completed':
        return 'Completed';
      case 'task.deleted':
        return 'Deleted';
      default:
        return eventType;
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) {
      return 'None';
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading audit trail...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>{error}</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Task History</h3>

        {/* Filter */}
        <div className={styles.filter}>
          <label className={styles.filterLabel}>Filter:</label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className={styles.filterSelect}
          >
            <option value="all">All Events</option>
            <option value="task.created">Created</option>
            <option value="task.updated">Updated</option>
            <option value="task.completed">Completed</option>
            <option value="task.deleted">Deleted</option>
          </select>
        </div>
      </div>

      {records.length === 0 ? (
        <div className={styles.emptyState}>
          <p>No audit records found</p>
        </div>
      ) : (
        <div className={styles.timeline}>
          {records.map((record) => {
            const isExpanded = expandedRecords.has(record.audit_id);
            const hasChanges = record.changes && Object.keys(record.changes).length > 0;

            return (
              <div key={record.audit_id} className={styles.record}>
                <div className={styles.recordHeader}>
                  <span className={styles.eventIcon}>
                    {getEventIcon(record.event_type)}
                  </span>
                  <div className={styles.recordInfo}>
                    <div className={styles.recordTitle}>
                      <span className={styles.eventLabel}>
                        {getEventLabel(record.event_type)}
                      </span>
                      {!taskId && (
                        <span className={styles.taskTitle}>
                          {record.task_title}
                        </span>
                      )}
                    </div>
                    <div className={styles.recordMeta}>
                      <span className={styles.timestamp}>
                        {formatTimestamp(record.timestamp)}
                      </span>
                      <span className={styles.source}>
                        via {record.source}
                      </span>
                    </div>
                  </div>

                  {hasChanges && (
                    <button
                      type="button"
                      onClick={() => toggleExpanded(record.audit_id)}
                      className={styles.expandButton}
                      aria-label={isExpanded ? 'Collapse' : 'Expand'}
                    >
                      {isExpanded ? '▼' : '▶'}
                    </button>
                  )}
                </div>

                {/* Changes Details */}
                {isExpanded && hasChanges && (
                  <div className={styles.changes}>
                    <h4 className={styles.changesTitle}>Changes:</h4>
                    <table className={styles.changesTable}>
                      <thead>
                        <tr>
                          <th>Field</th>
                          <th>Old Value</th>
                          <th>New Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(record.changes!).map(([field, change]) => (
                          <tr key={field}>
                            <td className={styles.fieldName}>{field}</td>
                            <td className={styles.oldValue}>
                              {formatValue(change.old_value)}
                            </td>
                            <td className={styles.newValue}>
                              {formatValue(change.new_value)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

/**
 * Compact audit trail for displaying in task details.
 */
interface CompactAuditTrailProps {
  userId: number;
  taskId: number;
  limit?: number;
}

export const CompactAuditTrail: React.FC<CompactAuditTrailProps> = ({
  userId,
  taskId,
  limit = 5,
}) => {
  return (
    <div className={styles.compact}>
      <AuditTrail userId={userId} taskId={taskId} limit={limit} />
    </div>
  );
};
