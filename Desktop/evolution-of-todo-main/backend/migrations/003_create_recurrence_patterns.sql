-- Migration: 003_create_recurrence_patterns.sql
-- Description: Create RecurrencePattern entity for recurring task support
-- Created: 2026-02-09
-- Feature: 002-event-driven-architecture
-- Note: This migration must run BEFORE 002_add_task_enhancements.sql applies foreign key constraints

-- Create frequency enum type
DO $$ BEGIN
    CREATE TYPE recurrence_frequency AS ENUM ('daily', 'weekly', 'monthly', 'custom');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create recurrence_patterns table
CREATE TABLE IF NOT EXISTS recurrence_patterns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    frequency recurrence_frequency NOT NULL,
    interval INTEGER NOT NULL DEFAULT 1,
    days_of_week INTEGER[],
    day_of_month INTEGER,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    last_generated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign key to users table
    CONSTRAINT fk_recurrence_patterns_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_recurrence_user_id ON recurrence_patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_recurrence_next_due ON recurrence_patterns(last_generated_at, start_date);
CREATE INDEX IF NOT EXISTS idx_recurrence_frequency ON recurrence_patterns(frequency);
CREATE INDEX IF NOT EXISTS idx_recurrence_active ON recurrence_patterns(start_date, end_date)
    WHERE end_date IS NULL OR end_date > NOW();

-- Add check constraints for validation
ALTER TABLE recurrence_patterns
    ADD CONSTRAINT chk_recurrence_interval_positive CHECK (interval >= 1),
    ADD CONSTRAINT chk_recurrence_days_of_week_range CHECK (
        days_of_week IS NULL OR
        (array_length(days_of_week, 1) BETWEEN 1 AND 7 AND
         days_of_week <@ ARRAY[0,1,2,3,4,5,6])
    ),
    ADD CONSTRAINT chk_recurrence_day_of_month_range CHECK (
        day_of_month IS NULL OR
        (day_of_month BETWEEN 1 AND 31)
    ),
    ADD CONSTRAINT chk_recurrence_end_after_start CHECK (
        end_date IS NULL OR end_date > start_date
    ),
    ADD CONSTRAINT chk_recurrence_weekly_has_days CHECK (
        frequency != 'weekly' OR days_of_week IS NOT NULL
    ),
    ADD CONSTRAINT chk_recurrence_monthly_has_day CHECK (
        frequency != 'monthly' OR day_of_month IS NOT NULL
    );

-- Add comments for documentation
COMMENT ON TABLE recurrence_patterns IS 'Defines how recurring tasks repeat';
COMMENT ON COLUMN recurrence_patterns.frequency IS 'Recurrence frequency: daily, weekly, monthly, or custom';
COMMENT ON COLUMN recurrence_patterns.interval IS 'Repeat every N units (e.g., every 2 weeks)';
COMMENT ON COLUMN recurrence_patterns.days_of_week IS 'Days of week for weekly patterns (0=Sunday, 6=Saturday)';
COMMENT ON COLUMN recurrence_patterns.day_of_month IS 'Day of month (1-31) for monthly patterns';
COMMENT ON COLUMN recurrence_patterns.start_date IS 'When to start generating task instances';
COMMENT ON COLUMN recurrence_patterns.end_date IS 'When to stop generating instances (optional)';
COMMENT ON COLUMN recurrence_patterns.last_generated_at IS 'Last time a task instance was generated';

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_recurrence_patterns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_recurrence_patterns_updated_at
    BEFORE UPDATE ON recurrence_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_recurrence_patterns_updated_at();

-- Migration complete
