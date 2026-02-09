/**
 * TodoList Component
 *
 * Displays list of todo tasks with actions
 */
import { useState } from 'react';
import styles from '../styles/Todos.module.css';
import { PriorityBadge, Priority } from './PrioritySelector';
import { TagList } from './TagInput';

export interface Todo {
  id: number;
  title: string;
  description: string | null;
  completed: boolean;
  user_id: number;
  created_at: string;
  updated_at: string;
  priority?: Priority;
  tags?: string[];
  due_date?: string;
  recurrence_pattern_id?: number;
}

interface TodoListProps {
  todos: Todo[];
  onTodoUpdated: () => Promise<void>;
  onTodoDeleted: () => Promise<void>;
}

export default function TodoList({ todos, onTodoUpdated, onTodoDeleted }: TodoListProps) {
  const [processingIds, setProcessingIds] = useState<Set<number>>(new Set());

  const handleToggle = async (id: number, currentCompleted: boolean) => {
    setProcessingIds(prev => new Set(prev).add(id));
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`/api/todos/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          completed: !currentCompleted,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update todo');
      }

      await onTodoUpdated();
    } catch (error) {
      console.error('Failed to toggle todo:', error);
      alert('Failed to update todo. Please try again.');
    } finally {
      setProcessingIds(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this task?')) {
      return;
    }

    setProcessingIds(prev => new Set(prev).add(id));
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch(`/api/todos/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete todo');
      }

      await onTodoDeleted();
    } catch (error) {
      console.error('Failed to delete todo:', error);
      alert('Failed to delete todo. Please try again.');
    } finally {
      setProcessingIds(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  if (todos.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No tasks yet. Create your first task above!</p>
      </div>
    );
  }

  return (
    <div className={styles.todoList}>
      {todos.map((todo) => {
        const isProcessing = processingIds.has(todo.id);
        const isCompleted = todo.completed;

        return (
          <div
            key={todo.id}
            className={`${styles.todoItem} ${isCompleted ? styles.completed : ''} ${isProcessing ? styles.processing : ''}`}
          >
            <div className={styles.todoCheckbox}>
              <input
                type="checkbox"
                checked={isCompleted}
                onChange={() => handleToggle(todo.id, todo.completed)}
                disabled={isProcessing}
                id={`todo-${todo.id}`}
              />
              <label htmlFor={`todo-${todo.id}`}></label>
            </div>

            <div className={styles.todoContent}>
              <div className={styles.todoHeader}>
                <h3 className={styles.todoTitle}>{todo.title}</h3>
                {todo.priority && (
                  <PriorityBadge priority={todo.priority} size="small" />
                )}
              </div>

              {todo.description && (
                <p className={styles.todoDescription}>{todo.description}</p>
              )}

              {todo.tags && todo.tags.length > 0 && (
                <div className={styles.todoTags}>
                  <TagList tags={todo.tags} size="small" maxVisible={5} />
                </div>
              )}

              <div className={styles.todoMeta}>
                <span className={styles.todoDate}>
                  Created: {new Date(todo.created_at).toLocaleDateString()}
                </span>
                {todo.due_date && (
                  <span className={styles.todoDueDate}>
                    Due: {new Date(todo.due_date).toLocaleDateString()}
                  </span>
                )}
                {todo.recurrence_pattern_id && (
                  <span className={styles.todoRecurring} title="Recurring task">
                    🔁
                  </span>
                )}
              </div>
            </div>

            <div className={styles.todoActions}>
              <button
                onClick={() => handleDelete(todo.id)}
                disabled={isProcessing}
                className={styles.deleteButton}
                aria-label="Delete task"
              >
                🗑️
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
