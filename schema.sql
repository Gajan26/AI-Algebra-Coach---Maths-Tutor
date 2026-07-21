-- AI Algebra Coach: PostgreSQL schema
-- Requires PostgreSQL 14+.

CREATE EXTENSION IF NOT EXISTS citext;

CREATE TYPE user_role AS ENUM ('student', 'teacher', 'admin');
CREATE TYPE message_sender AS ENUM ('student', 'coach', 'system');

CREATE TABLE users (
    id UUID PRIMARY KEY,
    role user_role NOT NULL DEFAULT 'student',
    email CITEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT users_email_not_blank CHECK (length(trim(email::text)) > 0)
);

CREATE TABLE coach_sessions (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    algebra_topic VARCHAR(120) NOT NULL,
    current_hint_level SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    CONSTRAINT coach_sessions_topic_not_blank CHECK (length(trim(algebra_topic)) > 0),
    CONSTRAINT coach_sessions_hint_level_range CHECK (current_hint_level BETWEEN 0 AND 5),
    CONSTRAINT coach_sessions_end_after_start CHECK (ended_at IS NULL OR ended_at >= created_at)
);

CREATE TABLE interaction_logs (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES coach_sessions(id) ON DELETE CASCADE,
    sender message_sender NOT NULL,
    chat_message TEXT NOT NULL,
    canvas_state_snapshot JSONB NOT NULL DEFAULT '{"steps": []}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT interaction_logs_message_not_blank CHECK (length(trim(chat_message)) > 0),
    CONSTRAINT interaction_logs_snapshot_is_object CHECK (jsonb_typeof(canvas_state_snapshot) = 'object')
);

CREATE INDEX coach_sessions_student_created_idx
    ON coach_sessions (student_id, created_at DESC);

CREATE INDEX coach_sessions_active_student_idx
    ON coach_sessions (student_id, updated_at DESC)
    WHERE ended_at IS NULL;

CREATE INDEX interaction_logs_session_created_idx
    ON interaction_logs (session_id, created_at ASC);

CREATE INDEX interaction_logs_canvas_state_gin_idx
    ON interaction_logs USING GIN (canvas_state_snapshot);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER coach_sessions_set_updated_at
BEFORE UPDATE ON coach_sessions
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
