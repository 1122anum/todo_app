/**
 * Chat Page for Phase III AI Chatbot
 *
 * Provides conversational interface for task management through AI assistant.
 * Requires authentication and integrates with Better Auth.
 */
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { ChatInterface } from '../components/ChatInterface';
import styles from '../styles/Chat.module.css';

export default function Chat() {
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { isAuthenticated, user, signout } = useAuth();
  const { showToast } = useToast();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/signin');
      return;
    }

    setLoading(false);
  }, [isAuthenticated, router]);

  const handleConversationStart = (newConversationId: string) => {
    setConversationId(newConversationId);
    showToast('Conversation started', 'success');
  };

  const handleNewConversation = () => {
    setConversationId(undefined);
    showToast('Starting new conversation', 'info');
  };

  const handleSignOut = async () => {
    try {
      await signout();
      showToast('Signed out successfully', 'success');
      router.push('/signin');
    } catch (error) {
      showToast('Failed to sign out', 'error');
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <h1 className={styles.title}>AI Todo Assistant</h1>
            <p className={styles.subtitle}>
              Chat with your AI assistant to manage tasks naturally
            </p>
          </div>
          <div className={styles.headerRight}>
            <span className={styles.userInfo}>
              Welcome, {user.email || 'User'}
            </span>
            <button
              onClick={handleNewConversation}
              className={styles.newConversationButton}
              disabled={!conversationId}
            >
              New Conversation
            </button>
            <button onClick={handleSignOut} className={styles.signOutButton}>
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <nav className={styles.nav}>
        <button
          onClick={() => router.push('/todos')}
          className={styles.navButton}
        >
          📋 Todo List
        </button>
        <button
          onClick={() => router.push('/chat')}
          className={`${styles.navButton} ${styles.navButtonActive}`}
        >
          💬 AI Chat
        </button>
      </nav>

      <main className={styles.main}>
        <div className={styles.chatWrapper}>
          <ChatInterface
            conversationId={conversationId}
            onConversationStart={handleConversationStart}
            userId={user.id?.toString() || ''}
          />
        </div>
      </main>

      <footer className={styles.footer}>
        <p>
          Powered by OpenAI • Phase III: AI-Powered Todo Chatbot
        </p>
      </footer>
    </div>
  );
}
