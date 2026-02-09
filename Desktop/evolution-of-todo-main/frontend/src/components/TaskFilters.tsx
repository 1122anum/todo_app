/**
 * TaskFilters component for filtering and sorting tasks.
 *
 * Features:
 * - Filter by priority (high/medium/low)
 * - Filter by tags (multiple selection)
 * - Filter by status (active/completed/all)
 * - Filter by due date (overdue/today/this week/no date)
 * - Sort by due date, priority, creation date
 * - Persist preferences in localStorage
 */
import React, { useState, useEffect } from 'react';
import styles from './TaskFilters.module.css';
import { Priority } from './PrioritySelector';

export interface FilterOptions {
  priorities: Priority[];
  tags: string[];
  status: 'all' | 'active' | 'completed';
  dueDate: 'all' | 'overdue' | 'today' | 'this-week' | 'no-date';
}

export interface SortOptions {
  field: 'due_date' | 'priority' | 'created_at' | 'title';
  order: 'asc' | 'desc';
}

interface TaskFiltersProps {
  availableTags: string[];
  onFilterChange: (filters: FilterOptions) => void;
  onSortChange: (sort: SortOptions) => void;
  initialFilters?: FilterOptions;
  initialSort?: SortOptions;
}

const DEFAULT_FILTERS: FilterOptions = {
  priorities: [],
  tags: [],
  status: 'active',
  dueDate: 'all',
};

const DEFAULT_SORT: SortOptions = {
  field: 'created_at',
  order: 'desc',
};

export const TaskFilters: React.FC<TaskFiltersProps> = ({
  availableTags,
  onFilterChange,
  onSortChange,
  initialFilters = DEFAULT_FILTERS,
  initialSort = DEFAULT_SORT,
}) => {
  const [filters, setFilters] = useState<FilterOptions>(initialFilters);
  const [sort, setSort] = useState<SortOptions>(initialSort);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  // Load preferences from localStorage on mount
  useEffect(() => {
    const savedFilters = localStorage.getItem('taskFilters');
    const savedSort = localStorage.getItem('taskSort');

    if (savedFilters) {
      try {
        const parsed = JSON.parse(savedFilters);
        setFilters(parsed);
        onFilterChange(parsed);
      } catch (error) {
        console.error('Failed to parse saved filters:', error);
      }
    }

    if (savedSort) {
      try {
        const parsed = JSON.parse(savedSort);
        setSort(parsed);
        onSortChange(parsed);
      } catch (error) {
        console.error('Failed to parse saved sort:', error);
      }
    }
  }, []);

  // Save preferences to localStorage when changed
  useEffect(() => {
    localStorage.setItem('taskFilters', JSON.stringify(filters));
    onFilterChange(filters);
  }, [filters, onFilterChange]);

  useEffect(() => {
    localStorage.setItem('taskSort', JSON.stringify(sort));
    onSortChange(sort);
  }, [sort, onSortChange]);

  const handlePriorityToggle = (priority: Priority) => {
    setFilters(prev => ({
      ...prev,
      priorities: prev.priorities.includes(priority)
        ? prev.priorities.filter(p => p !== priority)
        : [...prev.priorities, priority],
    }));
  };

  const handleTagToggle = (tag: string) => {
    setFilters(prev => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter(t => t !== tag)
        : [...prev.tags, tag],
    }));
  };

  const handleStatusChange = (status: FilterOptions['status']) => {
    setFilters(prev => ({ ...prev, status }));
  };

  const handleDueDateChange = (dueDate: FilterOptions['dueDate']) => {
    setFilters(prev => ({ ...prev, dueDate }));
  };

  const handleSortChange = (field: SortOptions['field']) => {
    setSort(prev => ({
      field,
      order: prev.field === field && prev.order === 'asc' ? 'desc' : 'asc',
    }));
  };

  const handleClearFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setSort(DEFAULT_SORT);
  };

  const hasActiveFilters =
    filters.priorities.length > 0 ||
    filters.tags.length > 0 ||
    filters.status !== 'active' ||
    filters.dueDate !== 'all';

  const getPriorityColor = (priority: Priority): string => {
    const colors = {
      high: '#ef4444',
      medium: '#f59e0b',
      low: '#10b981',
    };
    return colors[priority];
  };

  return (
    <div className={styles.container}>
      {/* Filter Header */}
      <div className={styles.header}>
        <button
          type="button"
          className={styles.toggleButton}
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          <span className={styles.toggleIcon}>{isExpanded ? '▼' : '▶'}</span>
          <span className={styles.toggleLabel}>
            Filters & Sort
            {hasActiveFilters && (
              <span className={styles.activeIndicator}>
                ({filters.priorities.length + filters.tags.length} active)
              </span>
            )}
          </span>
        </button>

        {hasActiveFilters && (
          <button
            type="button"
            className={styles.clearButton}
            onClick={handleClearFilters}
          >
            Clear All
          </button>
        )}
      </div>

      {/* Filter Content */}
      {isExpanded && (
        <div className={styles.content}>
          {/* Status Filter */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>Status</label>
            <div className={styles.buttonGroup}>
              {(['all', 'active', 'completed'] as const).map((status) => (
                <button
                  key={status}
                  type="button"
                  className={`${styles.filterButton} ${
                    filters.status === status ? styles.active : ''
                  }`}
                  onClick={() => handleStatusChange(status)}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Priority Filter */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>Priority</label>
            <div className={styles.buttonGroup}>
              {(['high', 'medium', 'low'] as Priority[]).map((priority) => (
                <button
                  key={priority}
                  type="button"
                  className={`${styles.filterButton} ${styles.priorityButton} ${
                    filters.priorities.includes(priority) ? styles.active : ''
                  }`}
                  style={{
                    borderColor: filters.priorities.includes(priority)
                      ? getPriorityColor(priority)
                      : undefined,
                    backgroundColor: filters.priorities.includes(priority)
                      ? `${getPriorityColor(priority)}15`
                      : undefined,
                  }}
                  onClick={() => handlePriorityToggle(priority)}
                >
                  {priority.charAt(0).toUpperCase() + priority.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Due Date Filter */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>Due Date</label>
            <div className={styles.buttonGroup}>
              {([
                { value: 'all', label: 'All' },
                { value: 'overdue', label: 'Overdue' },
                { value: 'today', label: 'Today' },
                { value: 'this-week', label: 'This Week' },
                { value: 'no-date', label: 'No Date' },
              ] as const).map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  className={`${styles.filterButton} ${
                    filters.dueDate === value ? styles.active : ''
                  }`}
                  onClick={() => handleDueDateChange(value)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Tag Filter */}
          {availableTags.length > 0 && (
            <div className={styles.section}>
              <label className={styles.sectionLabel}>Tags</label>
              <div className={styles.tagGrid}>
                {availableTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className={`${styles.tagButton} ${
                      filters.tags.includes(tag) ? styles.active : ''
                    }`}
                    onClick={() => handleTagToggle(tag)}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Sort Options */}
          <div className={styles.section}>
            <label className={styles.sectionLabel}>Sort By</label>
            <div className={styles.sortGroup}>
              {([
                { value: 'due_date', label: 'Due Date' },
                { value: 'priority', label: 'Priority' },
                { value: 'created_at', label: 'Created' },
                { value: 'title', label: 'Title' },
              ] as const).map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  className={`${styles.sortButton} ${
                    sort.field === value ? styles.active : ''
                  }`}
                  onClick={() => handleSortChange(value)}
                >
                  {label}
                  {sort.field === value && (
                    <span className={styles.sortIcon}>
                      {sort.order === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Apply filters to a list of tasks (client-side filtering).
 */
export function applyFilters<T extends {
  priority?: Priority;
  tags?: string[];
  completed: boolean;
  due_date?: string;
}>(tasks: T[], filters: FilterOptions): T[] {
  return tasks.filter(task => {
    // Status filter
    if (filters.status === 'active' && task.completed) return false;
    if (filters.status === 'completed' && !task.completed) return false;

    // Priority filter
    if (filters.priorities.length > 0) {
      if (!task.priority || !filters.priorities.includes(task.priority)) {
        return false;
      }
    }

    // Tag filter (task must have ALL selected tags)
    if (filters.tags.length > 0) {
      if (!task.tags || !filters.tags.every(tag => task.tags!.includes(tag))) {
        return false;
      }
    }

    // Due date filter
    if (filters.dueDate !== 'all') {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const dueDate = task.due_date ? new Date(task.due_date) : null;

      if (filters.dueDate === 'no-date' && dueDate !== null) return false;
      if (filters.dueDate !== 'no-date' && dueDate === null) return false;

      if (dueDate) {
        const dueDateOnly = new Date(dueDate.getFullYear(), dueDate.getMonth(), dueDate.getDate());

        if (filters.dueDate === 'overdue' && dueDateOnly >= today) return false;
        if (filters.dueDate === 'today' && dueDateOnly.getTime() !== today.getTime()) return false;
        if (filters.dueDate === 'this-week') {
          const weekFromNow = new Date(today);
          weekFromNow.setDate(weekFromNow.getDate() + 7);
          if (dueDateOnly < today || dueDateOnly > weekFromNow) return false;
        }
      }
    }

    return true;
  });
}

/**
 * Apply sorting to a list of tasks (client-side sorting).
 */
export function applySort<T extends {
  priority?: Priority;
  created_at: string;
  due_date?: string;
  title: string;
}>(tasks: T[], sort: SortOptions): T[] {
  const priorityOrder: Record<Priority, number> = {
    high: 3,
    medium: 2,
    low: 1,
  };

  return [...tasks].sort((a, b) => {
    let comparison = 0;

    switch (sort.field) {
      case 'due_date':
        const aDate = a.due_date ? new Date(a.due_date).getTime() : Infinity;
        const bDate = b.due_date ? new Date(b.due_date).getTime() : Infinity;
        comparison = aDate - bDate;
        break;

      case 'priority':
        const aPriority = a.priority ? priorityOrder[a.priority] : 0;
        const bPriority = b.priority ? priorityOrder[b.priority] : 0;
        comparison = bPriority - aPriority; // Higher priority first
        break;

      case 'created_at':
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        break;

      case 'title':
        comparison = a.title.localeCompare(b.title);
        break;
    }

    return sort.order === 'asc' ? comparison : -comparison;
  });
}
