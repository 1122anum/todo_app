import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import AddTodo from '../components/AddTodo';
import TodoList from '../components/TodoList';
import styles from '../styles/Todos.module.css';

interface Todo {
  id: number;
  title: string;
  description: string | null;
  completed: boolean;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export default function Todos() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();
  const { isAuthenticated, user, signout } = useAuth();
  const { showToast } = useToast();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/signin');
      return;
    }

    fetchTodos();
  }, [isAuthenticated, router]);

  const fetchTodos = async () => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch('/api/todos', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        showToast('error', 'Session expired', 'Please sign in again');
        signout();
        router.push('/signin');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch todos');
      }

      const data = await response.json();
      setTodos(data);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to load todos';
      setError(errorMsg);
      showToast('error', 'Failed to load todos', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSignout = () => {
    signout();
    showToast('success', 'Signed out', 'See you next time!');
    router.push('/signin');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Evolution of Todo (VERIFICATION_STRING)</h1>
          <div className={styles.userInfo}>
            <span className={styles.email}>{user?.email}</span>
            <button onClick={handleSignout} className={styles.signoutButton}>
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <nav className={styles.nav}>
        <button
          onClick={() => router.push('/todos')}
          className={`${styles.navButton} ${styles.navButtonActive}`}
        >
          📋 Todo List
        </button>
        <button
          onClick={() => router.push('/chat')}
          className={styles.navButton}
        >
          💬 AI Chat
        </button>
      </nav>

      <main className={styles.main}>
        <AddTodo onTodoAdded={fetchTodos} />

        {loading && <div className={styles.loading}>Loading your todos...</div>}

        {error && <div className={styles.error}>{error}</div>}

        {!loading && !error && (
          <TodoList
            todos={todos}
            onTodoUpdated={fetchTodos}
            onTodoDeleted={fetchTodos}
          />
        )}
      </main>
    </div>
  );
}
