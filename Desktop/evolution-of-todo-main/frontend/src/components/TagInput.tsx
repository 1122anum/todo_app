/**
 * TagInput component for adding and managing task tags.
 *
 * Features:
 * - Autocomplete suggestions based on existing tags
 * - Tag chips with remove functionality
 * - Keyboard navigation (Enter to add, Backspace to remove)
 * - Usage-based sorting (most used tags first)
 */
import React, { useState, useEffect, useRef } from 'react';
import styles from './TagInput.module.css';

export interface Tag {
  id: number;
  name: string;
  color?: string;
  usage_count: number;
}

interface TagInputProps {
  value: string[];  // Array of tag names
  onChange: (tags: string[]) => void;
  disabled?: boolean;
  placeholder?: string;
  maxTags?: number;
}

export const TagInput: React.FC<TagInputProps> = ({
  value = [],
  onChange,
  disabled = false,
  placeholder = 'Add tags...',
  maxTags = 10,
}) => {
  const [inputValue, setInputValue] = useState<string>('');
  const [suggestions, setSuggestions] = useState<Tag[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Fetch autocomplete suggestions
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (inputValue.trim().length === 0) {
        setSuggestions([]);
        setShowSuggestions(false);
        return;
      }

      try {
        // TODO: Replace with actual API endpoint when integrated
        // For now, using mock data structure
        const response = await fetch(
          `/api/todos/tags/autocomplete?query=${encodeURIComponent(inputValue)}`
        );

        if (response.ok) {
          const data: Tag[] = await response.json();
          // Filter out already selected tags
          const filtered = data.filter(tag => !value.includes(tag.name));
          setSuggestions(filtered);
          setShowSuggestions(filtered.length > 0);
          setSelectedIndex(-1);
        }
      } catch (error) {
        console.error('Failed to fetch tag suggestions:', error);
        setSuggestions([]);
        setShowSuggestions(false);
      }
    };

    const debounceTimer = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(debounceTimer);
  }, [inputValue, value]);

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const addTag = (tagName: string) => {
    const normalized = tagName.trim().toLowerCase();

    if (!normalized) {
      return;
    }

    if (normalized.length > 50) {
      alert('Tag name cannot exceed 50 characters');
      return;
    }

    if (value.includes(normalized)) {
      alert('Tag already added');
      return;
    }

    if (value.length >= maxTags) {
      alert(`Maximum ${maxTags} tags allowed`);
      return;
    }

    onChange([...value, normalized]);
    setInputValue('');
    setShowSuggestions(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  const removeTag = (tagName: string) => {
    onChange(value.filter(tag => tag !== tagName));
    inputRef.current?.focus();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        // Add selected suggestion
        addTag(suggestions[selectedIndex].name);
      } else if (inputValue.trim()) {
        // Add typed value
        addTag(inputValue);
      }
    } else if (e.key === 'Backspace' && inputValue === '' && value.length > 0) {
      // Remove last tag when backspace on empty input
      e.preventDefault();
      removeTag(value[value.length - 1]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (showSuggestions && suggestions.length > 0) {
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (showSuggestions && suggestions.length > 0) {
        setSelectedIndex(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }
  };

  const handleSuggestionClick = (tag: Tag) => {
    addTag(tag.name);
  };

  const getTagColor = (tagName: string): string => {
    // Find tag in suggestions to get its color
    const tag = suggestions.find(t => t.name === tagName);
    return tag?.color || '#6b7280';
  };

  return (
    <div className={styles.container}>
      <label className={styles.label}>Tags</label>

      {/* Tag chips */}
      <div className={styles.tagsContainer}>
        {value.map((tag) => (
          <span
            key={tag}
            className={styles.tagChip}
            style={{
              backgroundColor: `${getTagColor(tag)}15`,
              borderColor: getTagColor(tag),
              color: getTagColor(tag),
            }}
          >
            <span className={styles.tagName}>{tag}</span>
            {!disabled && (
              <button
                type="button"
                className={styles.removeButton}
                onClick={() => removeTag(tag)}
                aria-label={`Remove tag ${tag}`}
              >
                ×
              </button>
            )}
          </span>
        ))}

        {/* Input field */}
        {!disabled && value.length < maxTags && (
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => inputValue && setShowSuggestions(suggestions.length > 0)}
            placeholder={value.length === 0 ? placeholder : ''}
            className={styles.input}
            disabled={disabled}
            aria-label="Add tag"
            aria-autocomplete="list"
            aria-controls="tag-suggestions"
            aria-expanded={showSuggestions}
          />
        )}
      </div>

      {/* Autocomplete suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          id="tag-suggestions"
          className={styles.suggestions}
          role="listbox"
        >
          {suggestions.map((tag, index) => (
            <button
              key={tag.id}
              type="button"
              className={`${styles.suggestion} ${
                index === selectedIndex ? styles.selected : ''
              }`}
              onClick={() => handleSuggestionClick(tag)}
              role="option"
              aria-selected={index === selectedIndex}
            >
              <span
                className={styles.suggestionDot}
                style={{ backgroundColor: tag.color || '#6b7280' }}
              />
              <span className={styles.suggestionName}>{tag.name}</span>
              <span className={styles.suggestionCount}>
                {tag.usage_count} {tag.usage_count === 1 ? 'use' : 'uses'}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Helper text */}
      <p className={styles.hint}>
        Press Enter to add, Backspace to remove last tag
        {maxTags && ` (${value.length}/${maxTags})`}
      </p>
    </div>
  );
};

/**
 * TagChip component for displaying a single tag (read-only).
 */
interface TagChipProps {
  tag: string;
  color?: string;
  size?: 'small' | 'medium' | 'large';
  onRemove?: () => void;
}

export const TagChip: React.FC<TagChipProps> = ({
  tag,
  color = '#6b7280',
  size = 'medium',
  onRemove,
}) => {
  return (
    <span
      className={`${styles.tagChip} ${styles[size]}`}
      style={{
        backgroundColor: `${color}15`,
        borderColor: color,
        color: color,
      }}
    >
      <span className={styles.tagName}>{tag}</span>
      {onRemove && (
        <button
          type="button"
          className={styles.removeButton}
          onClick={onRemove}
          aria-label={`Remove tag ${tag}`}
        >
          ×
        </button>
      )}
    </span>
  );
};

/**
 * TagList component for displaying multiple tags (read-only).
 */
interface TagListProps {
  tags: string[];
  colors?: Record<string, string>;
  size?: 'small' | 'medium' | 'large';
  maxVisible?: number;
}

export const TagList: React.FC<TagListProps> = ({
  tags,
  colors = {},
  size = 'medium',
  maxVisible,
}) => {
  const visibleTags = maxVisible ? tags.slice(0, maxVisible) : tags;
  const hiddenCount = maxVisible && tags.length > maxVisible ? tags.length - maxVisible : 0;

  if (tags.length === 0) {
    return null;
  }

  return (
    <div className={styles.tagList}>
      {visibleTags.map((tag) => (
        <TagChip
          key={tag}
          tag={tag}
          color={colors[tag]}
          size={size}
        />
      ))}
      {hiddenCount > 0 && (
        <span className={`${styles.tagChip} ${styles[size]} ${styles.moreChip}`}>
          +{hiddenCount} more
        </span>
      )}
    </div>
  );
};
