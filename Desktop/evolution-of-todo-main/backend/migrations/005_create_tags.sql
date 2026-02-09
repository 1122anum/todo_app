-- Migration: 005_create_tags.sql
-- Description: Create Tag entity for task categorization
-- Created: 2026-02-09
-- Feature: 002-event-driven-architecture

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7),
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign key constraint
    CONSTRAINT fk_tags_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    -- Unique constraint: tag name must be unique per user
    CONSTRAINT uq_tags_user_name UNIQUE (user_id, name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(user_id, name);
CREATE INDEX IF NOT EXISTS idx_tags_usage_count ON tags(usage_count) WHERE usage_count > 0;

-- Add check constraints for validation
ALTER TABLE tags
    ADD CONSTRAINT chk_tags_name_length CHECK (char_length(name) BETWEEN 1 AND 50),
    ADD CONSTRAINT chk_tags_name_format CHECK (name ~ '^[a-zA-Z0-9 \-]+$'),
    ADD CONSTRAINT chk_tags_color_format CHECK (
        color IS NULL OR color ~ '^#[0-9A-Fa-f]{6}$'
    ),
    ADD CONSTRAINT chk_tags_usage_count_non_negative CHECK (usage_count >= 0);

-- Add comments for documentation
COMMENT ON TABLE tags IS 'Custom labels for organizing tasks';
COMMENT ON COLUMN tags.user_id IS 'Owner of the tag';
COMMENT ON COLUMN tags.name IS 'Tag name (unique per user, 1-50 chars, alphanumeric + spaces/hyphens)';
COMMENT ON COLUMN tags.color IS 'Hex color code for visual display (e.g., #FF5733)';
COMMENT ON COLUMN tags.usage_count IS 'Number of tasks currently using this tag';

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_tags_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tags_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION update_tags_updated_at();

-- Create function to update tag usage_count when tasks change
CREATE OR REPLACE FUNCTION update_tag_usage_count()
RETURNS TRIGGER AS $$
DECLARE
    tag_name TEXT;
    old_tags TEXT[];
    new_tags TEXT[];
BEGIN
    -- Handle INSERT: increment usage_count for new tags
    IF TG_OP = 'INSERT' THEN
        FOREACH tag_name IN ARRAY NEW.tags
        LOOP
            -- Create tag if it doesn't exist
            INSERT INTO tags (user_id, name, usage_count)
            VALUES (NEW.user_id, tag_name, 1)
            ON CONFLICT (user_id, name)
            DO UPDATE SET usage_count = tags.usage_count + 1;
        END LOOP;
        RETURN NEW;
    END IF;

    -- Handle UPDATE: adjust usage_count for added/removed tags
    IF TG_OP = 'UPDATE' THEN
        old_tags := COALESCE(OLD.tags, ARRAY[]::TEXT[]);
        new_tags := COALESCE(NEW.tags, ARRAY[]::TEXT[]);

        -- Decrement for removed tags
        FOREACH tag_name IN ARRAY old_tags
        LOOP
            IF NOT (tag_name = ANY(new_tags)) THEN
                UPDATE tags
                SET usage_count = GREATEST(usage_count - 1, 0)
                WHERE user_id = OLD.user_id AND name = tag_name;
            END IF;
        END LOOP;

        -- Increment for added tags
        FOREACH tag_name IN ARRAY new_tags
        LOOP
            IF NOT (tag_name = ANY(old_tags)) THEN
                INSERT INTO tags (user_id, name, usage_count)
                VALUES (NEW.user_id, tag_name, 1)
                ON CONFLICT (user_id, name)
                DO UPDATE SET usage_count = tags.usage_count + 1;
            END IF;
        END LOOP;

        RETURN NEW;
    END IF;

    -- Handle DELETE: decrement usage_count for all tags
    IF TG_OP = 'DELETE' THEN
        FOREACH tag_name IN ARRAY OLD.tags
        LOOP
            UPDATE tags
            SET usage_count = GREATEST(usage_count - 1, 0)
            WHERE user_id = OLD.user_id AND name = tag_name;
        END LOOP;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tag_usage_count
    AFTER INSERT OR UPDATE OF tags OR DELETE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_tag_usage_count();

-- Migration complete
