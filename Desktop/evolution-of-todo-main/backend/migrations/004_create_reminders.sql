-- Migration: 004_create_reminders.sql
-- Description: Create Reminder entity for task notifications
-- Created: 2026-02-09
-- Feature: 002-event-driven-architecture

-- Create notification_channel enum type
DO $$ BEGIN
    CREATE TYPE notification_channel AS ENUM ('in_app');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create reminder_status enum type
DO $$ BEGIN
    CREATE TYPE reminder_status AS ENUM ('pending', 'sent', 'snoozed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create reminders table
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    notification_channel notification_channel NOT NULL DEFAULT 'in_app',
    status reminder_status NOT NULL DEFAULT 'pending',
    snoozed_until TIMESTAMP,
    sent_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign key constraints
    CONSTRAINT fk_reminders_task
        FOREIGN KEY (task_id)
        REFERENCES tasks(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_reminders_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_reminders_task_id ON reminders(task_id);
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_scheduled_time_status ON reminders(scheduled_time, status)
    WHERE status IN ('pending', 'snoozed');
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(scheduled_time)
    WHERE status = 'pending' AND scheduled_time <= NOW();
CREATE INDEX IF NOT EXISTS idx_reminders_snoozed ON reminders(snoozed_until)
    WHERE status = 'snoozed' AND snoozed_until IS NOT NULL;

-- Add check constraints for validation
ALTER TABLE reminders
    ADD CONSTRAINT chk_reminders_snoozed_has_until CHECK (
        status != 'snoozed' OR snoozed_until IS NOT NULL
    ),
    ADD CONSTRAINT chk_reminders_snoozed_after_scheduled CHECK (
        snoozed_until IS NULL OR snoozed_until > scheduled_time
    ),
    ADD CONSTRAINT chk_reminders_sent_has_timestamp CHECK (
        status != 'sent' OR sent_at IS NOT NULL
    );

-- Add comments for documentation
COMMENT ON TABLE reminders IS 'Scheduled notifications for tasks';
COMMENT ON COLUMN reminders.task_id IS 'Associated task for this reminder';
COMMENT ON COLUMN reminders.user_id IS 'Owner of the reminder';
COMMENT ON COLUMN reminders.scheduled_time IS 'When to send the reminder notification';
COMMENT ON COLUMN reminders.notification_channel IS 'Notification channel (in_app only in Phase V)';
COMMENT ON COLUMN reminders.status IS 'Reminder status: pending, sent, snoozed, or cancelled';
COMMENT ON COLUMN reminders.snoozed_until IS 'When to re-trigger reminder if snoozed';
COMMENT ON COLUMN reminders.sent_at IS 'When the reminder was actually sent';

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_reminders_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_reminders_updated_at
    BEFORE UPDATE ON reminders
    FOR EACH ROW
    EXECUTE FUNCTION update_reminders_updated_at();

-- Create function to automatically create reminder when task has due_date
CREATE OR REPLACE FUNCTION create_reminder_for_task()
RETURNS TRIGGER AS $$
BEGIN
    -- If task has due_date and no reminder exists, create one (1 hour before due)
    IF NEW.due_date IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM reminders WHERE task_id = NEW.id
    ) THEN
        INSERT INTO reminders (task_id, user_id, scheduled_time, notification_channel, status)
        VALUES (
            NEW.id,
            NEW.user_id,
            NEW.due_date - INTERVAL '1 hour',
            'in_app',
            'pending'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_reminder_for_task
    AFTER INSERT OR UPDATE OF due_date ON tasks
    FOR EACH ROW
    WHEN (NEW.due_date IS NOT NULL)
    EXECUTE FUNCTION create_reminder_for_task();

-- Migration complete
