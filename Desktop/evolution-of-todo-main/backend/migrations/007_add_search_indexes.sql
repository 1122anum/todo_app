-- Migration: Add indexes for search, filter, and sort performance
-- Task: T059 [US4] Add database indexes for search performance
-- Date: 2026-02-09

-- Add index on title for search performance (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_tasks_title_lower ON tasks (LOWER(title));

-- Add index on description for search performance (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_tasks_description_lower ON tasks (LOWER(description));

-- Add index on due_date for filtering and sorting
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks (due_date);

-- Add index on priority for filtering and sorting
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority);

-- Add composite index for common query patterns (user_id + completed + due_date)
CREATE INDEX IF NOT EXISTS idx_tasks_user_completed_due ON tasks (user_id, completed, due_date);

-- Add composite index for user_id + priority (common filter combination)
CREATE INDEX IF NOT EXISTS idx_tasks_user_priority ON tasks (user_id, priority);

-- Add GIN index for tags array (for efficient tag filtering)
CREATE INDEX IF NOT EXISTS idx_tasks_tags_gin ON tasks USING GIN (tags);

-- Add index on created_at for sorting (if not already exists)
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks (created_at DESC);

-- Performance notes:
-- 1. LOWER() indexes enable case-insensitive search without full table scan
-- 2. Composite indexes optimize multi-column WHERE clauses
-- 3. GIN index on tags array enables efficient containment queries
-- 4. DESC index on created_at optimizes default sort order
-- 5. These indexes will be used automatically by PostgreSQL query planner

-- Verify indexes were created
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'tasks'
ORDER BY indexname;
