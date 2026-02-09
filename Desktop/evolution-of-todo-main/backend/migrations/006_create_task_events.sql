-- Migration: 006_create_task_events.sql
-- Description: Create TaskEvent entity for immutable audit trail
-- Created: 2026-02-09
-- Feature: 002-event-driven-architecture

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create event_type enum
DO $$ BEGIN
    CREATE TYPE task_event_type AS ENUM ('created', 'updated', 'deleted', 'completed', 'uncompleted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create task_events table (partitioned by timestamp for scalability)
CREATE TABLE IF NOT EXISTS task_events (
    id BIGSERIAL,
    event_id UUID NOT NULL,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    event_type task_event_type NOT NULL,
    changes JSONB NOT NULL,
    metadata JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign key constraint (user only, task may be deleted)
    CONSTRAINT fk_task_events_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    -- Primary key includes timestamp for partitioning
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create unique constraint on event_id to prevent duplicate processing
CREATE UNIQUE INDEX IF NOT EXISTS idx_task_events_event_id ON task_events(event_id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_task_events_task_id_timestamp ON task_events(task_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_task_events_user_id_timestamp ON task_events(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_task_events_timestamp ON task_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_task_events_event_type ON task_events(event_type);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_task_events_changes ON task_events USING GIN(changes);
CREATE INDEX IF NOT EXISTS idx_task_events_metadata ON task_events USING GIN(metadata);

-- Add check constraints for validation
ALTER TABLE task_events
    ADD CONSTRAINT chk_task_events_changes_not_empty CHECK (jsonb_typeof(changes) = 'object'),
    ADD CONSTRAINT chk_task_events_metadata_has_source CHECK (metadata ? 'source'),
    ADD CONSTRAINT chk_task_events_metadata_has_correlation_id CHECK (metadata ? 'correlation_id');

-- Add comments for documentation
COMMENT ON TABLE task_events IS 'Immutable audit trail of all task changes';
COMMENT ON COLUMN task_events.event_id IS 'Unique event UUID from Kafka (prevents duplicate processing)';
COMMENT ON COLUMN task_events.task_id IS 'Associated task (may be deleted)';
COMMENT ON COLUMN task_events.user_id IS 'User who made the change';
COMMENT ON COLUMN task_events.event_type IS 'Type of change: created, updated, deleted, completed, uncompleted';
COMMENT ON COLUMN task_events.changes IS 'JSONB object with field_name: {old_value, new_value}';
COMMENT ON COLUMN task_events.metadata IS 'JSONB with source, correlation_id, and other metadata';
COMMENT ON COLUMN task_events.timestamp IS 'When the change occurred';

-- Create initial partition for current month
DO $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE);
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'task_events_' || to_char(start_date, 'YYYY_MM');

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF task_events
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        start_date,
        end_date
    );
END $$;

-- Create function to automatically create monthly partitions
CREATE OR REPLACE FUNCTION create_task_events_partition()
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Create partition for next month
    start_date := date_trunc('month', CURRENT_DATE + INTERVAL '1 month');
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'task_events_' || to_char(start_date, 'YYYY_MM');

    -- Check if partition already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF task_events
             FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            start_date,
            end_date
        );
        RAISE NOTICE 'Created partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create function to archive old partitions (90+ days retention)
CREATE OR REPLACE FUNCTION archive_old_task_events_partitions()
RETURNS void AS $$
DECLARE
    partition_record RECORD;
    retention_date DATE;
BEGIN
    retention_date := CURRENT_DATE - INTERVAL '90 days';

    FOR partition_record IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE 'task_events_%'
        AND tablename < 'task_events_' || to_char(retention_date, 'YYYY_MM')
    LOOP
        -- Detach partition (makes it a regular table for archival)
        EXECUTE format('ALTER TABLE task_events DETACH PARTITION %I', partition_record.tablename);
        RAISE NOTICE 'Detached old partition: %', partition_record.tablename;

        -- Optionally: Move to archive schema or drop
        -- EXECUTE format('DROP TABLE %I', partition_record.tablename);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Prevent updates and deletes on task_events (immutable audit trail)
CREATE OR REPLACE FUNCTION prevent_task_events_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'task_events table is immutable - updates and deletes are not allowed';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_prevent_task_events_update
    BEFORE UPDATE ON task_events
    FOR EACH ROW
    EXECUTE FUNCTION prevent_task_events_modification();

CREATE TRIGGER trigger_prevent_task_events_delete
    BEFORE DELETE ON task_events
    FOR EACH ROW
    EXECUTE FUNCTION prevent_task_events_modification();

-- Migration complete
