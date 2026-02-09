-- Migration: 002_add_task_enhancements.sql
-- Description: Add advanced features to Task entity (priority, due_date, tags, recurrence support)
-- Created: 2026-02-09
-- Feature: 002-event-driven-architecture

-- Add priority enum type
DO $$ BEGIN
    CREATE TYPE task_priority AS ENUM ('high', 'medium', 'low');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add new columns to tasks table
ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS priority task_priority NOT NULL DEFAULT 'medium',
    ADD COLUMN IF NOT EXISTS due_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS recurrence_pattern_id INTEGER,
    ADD COLUMN IF NOT EXISTS is_recurring_instance BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS parent_task_id INTEGER;

-- Add foreign key constraints
ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_recurrence_pattern
        FOREIGN KEY (recurrence_pattern_id)
        REFERENCES recurrence_patterns(id)
        ON DELETE SET NULL,
    ADD CONSTRAINT fk_tasks_parent_task
        FOREIGN KEY (parent_task_id)
        REFERENCES tasks(id)
        ON DELETE CASCADE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_recurrence_pattern_id ON tasks(recurrence_pattern_id) WHERE recurrence_pattern_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id) WHERE parent_task_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_completed_due_date ON tasks(completed, due_date) WHERE due_date IS NOT NULL;

-- Add check constraints
ALTER TABLE tasks
    ADD CONSTRAINT chk_tasks_title_length CHECK (char_length(title) BETWEEN 1 AND 255),
    ADD CONSTRAINT chk_tasks_description_length CHECK (description IS NULL OR char_length(description) <= 2000),
    ADD CONSTRAINT chk_tasks_tags_count CHECK (array_length(tags, 1) IS NULL OR array_length(tags, 1) <= 10),
    ADD CONSTRAINT chk_tasks_recurring_instance_has_parent CHECK (
        (is_recurring_instance = FALSE) OR
        (is_recurring_instance = TRUE AND parent_task_id IS NOT NULL)
    );

-- Add comments for documentation
COMMENT ON COLUMN tasks.priority IS 'Task priority level: high, medium, or low';
COMMENT ON COLUMN tasks.due_date IS 'When the task is due (optional)';
COMMENT ON COLUMN tasks.tags IS 'Array of tag names for categorization (max 10 tags)';
COMMENT ON COLUMN tasks.recurrence_pattern_id IS 'Link to recurrence pattern if this is a recurring task parent';
COMMENT ON COLUMN tasks.is_recurring_instance IS 'True if this task was generated from a recurrence pattern';
COMMENT ON COLUMN tasks.parent_task_id IS 'Link to parent recurring task if this is an instance';

-- Update updated_at trigger to include new columns
CREATE OR REPLACE FUNCTION update_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_tasks_updated_at ON tasks;
CREATE TRIGGER trigger_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_tasks_updated_at();

-- Migration complete
