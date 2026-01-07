-- =============================================================================
-- Schema for Self Development App
-- This script creates the necessary tables for Django models
-- =============================================================================

-- Users table (Django's auth_user)
CREATE TABLE IF NOT EXISTS auth_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks_task (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'todo',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_period VARCHAR(20),
    recurrence_target_count INTEGER DEFAULT 1,
    recurrence_end_date DATE,
    estimated_duration INTEGER,
    tags VARCHAR(500) NOT NULL DEFAULT ''
);

-- Task completions table
CREATE TABLE IF NOT EXISTS tasks_taskcompletion (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks_task(id) ON DELETE CASCADE,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    notes TEXT NOT NULL DEFAULT '',
    duration_minutes INTEGER
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tasks_task_status ON tasks_task(status);
CREATE INDEX IF NOT EXISTS idx_tasks_task_priority ON tasks_task(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_task_due_date ON tasks_task(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_task_user_status ON tasks_task(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_task_is_recurring ON tasks_task(is_recurring);
CREATE INDEX IF NOT EXISTS idx_tasks_taskcompletion_task_completed ON tasks_taskcompletion(task_id, completed_at);
CREATE INDEX IF NOT EXISTS idx_tasks_taskcompletion_completed_at ON tasks_taskcompletion(completed_at);

-- Django migrations tracking table
CREATE TABLE IF NOT EXISTS django_migrations (
    id SERIAL PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Django content types (required for admin)
CREATE TABLE IF NOT EXISTS django_content_type (
    id SERIAL PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    UNIQUE(app_label, model)
);

-- Insert content types
INSERT INTO django_content_type (app_label, model) VALUES
    ('auth', 'user'),
    ('tasks', 'task'),
    ('tasks', 'taskcompletion')
ON CONFLICT DO NOTHING;

-- Mark migrations as applied
INSERT INTO django_migrations (app, name) VALUES
    ('contenttypes', '0001_initial'),
    ('contenttypes', '0002_remove_content_type_name'),
    ('auth', '0001_initial'),
    ('auth', '0002_alter_permission_name_max_length'),
    ('auth', '0003_alter_user_email_max_length'),
    ('auth', '0004_alter_user_username_opts'),
    ('auth', '0005_alter_user_last_login_null'),
    ('auth', '0006_require_contenttypes_0002'),
    ('auth', '0007_alter_validators_add_error_messages'),
    ('auth', '0008_alter_user_username_max_length'),
    ('auth', '0009_alter_user_last_name_max_length'),
    ('auth', '0010_alter_group_name_max_length'),
    ('auth', '0011_update_proxy_permissions'),
    ('auth', '0012_alter_user_first_name_max_length'),
    ('tasks', '0001_initial')
ON CONFLICT DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Schema created successfully!'; END $$;

