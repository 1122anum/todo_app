/**
 * SearchBar component for live task search.
 *
 * Features:
 * - Real-time search with debouncing (300ms)
 * - Search in task title and description
 * - Loading indicator during search
 * - Clear search button
 * - Keyboard shortcuts (Escape to clear)
 * - Search results count
 */
import React, { useState, useEffect, useRef } from 'react';
import styles from './SearchBar.module.css';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  debounceMs?: number;
  isLoading?: boolean;
  resultCount?: number;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  placeholder = 'Search tasks...',
  debounceMs = 300,
  isLoading = false,
  resultCount,
}) => {
  const [query, setQuery] = useState<string>('');
  const [isFocused, setIsFocused] = useState<boolean>(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced search effect
  useEffect(() => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      onSearch(query);
    }, debounceMs);

    // Cleanup
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [query, debounceMs, onSearch]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  const handleClear = () => {
    setQuery('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      handleClear();
    }
  };

  const handleFocus = () => {
    setIsFocused(true);
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  return (
    <div className={styles.container}>
      <div
        className={`${styles.searchBox} ${isFocused ? styles.focused : ''} ${
          isLoading ? styles.loading : ''
        }`}
      >
        {/* Search Icon */}
        <span className={styles.searchIcon} aria-hidden="true">
          🔍
        </span>

        {/* Input Field */}
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          className={styles.input}
          aria-label="Search tasks"
          aria-describedby={resultCount !== undefined ? 'search-results-count' : undefined}
        />

        {/* Loading Spinner */}
        {isLoading && (
          <span className={styles.spinner} aria-label="Searching...">
            ⏳
          </span>
        )}

        {/* Clear Button */}
        {query && !isLoading && (
          <button
            type="button"
            onClick={handleClear}
            className={styles.clearButton}
            aria-label="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      {/* Results Count */}
      {query && resultCount !== undefined && !isLoading && (
        <div id="search-results-count" className={styles.resultsCount}>
          {resultCount === 0 ? (
            <span className={styles.noResults}>No tasks found</span>
          ) : (
            <span className={styles.hasResults}>
              {resultCount} {resultCount === 1 ? 'task' : 'tasks'} found
            </span>
          )}
        </div>
      )}

      {/* Search Tips */}
      {isFocused && !query && (
        <div className={styles.searchTips}>
          <p className={styles.tipText}>
            💡 Search by task title or description. Press <kbd>Esc</kbd> to clear.
          </p>
        </div>
      )}
    </div>
  );
};

/**
 * Hook for managing search state and API calls.
 *
 * Usage:
 * const { query, setQuery, results, isLoading } = useTaskSearch();
 */
export function useTaskSearch() {
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      if (!query.trim()) {
        setResults([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          throw new Error('Not authenticated');
        }

        const params = new URLSearchParams({
          search: query,
          limit: '100',
        });

        const response = await fetch(`/api/todos?${params}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Search failed');
        }

        const data = await response.json();
        setResults(data);
      } catch (err) {
        console.error('Search error:', err);
        setError(err instanceof Error ? err.message : 'Search failed');
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [query]);

  return {
    query,
    setQuery,
    results,
    isLoading,
    error,
    resultCount: results.length,
  };
}

/**
 * Highlight search matches in text.
 */
export function highlightMatches(text: string, query: string): React.ReactNode {
  if (!query.trim()) {
    return text;
  }

  const regex = new RegExp(`(${query})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) =>
    regex.test(part) ? (
      <mark key={index} className={styles.highlight}>
        {part}
      </mark>
    ) : (
      <span key={index}>{part}</span>
    )
  );
}
