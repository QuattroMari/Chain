CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    has_motion BOOLEAN NOT NULL,
    motion_score FLOAT,
    processing_time FLOAT,
    status VARCHAR(50) DEFAULT 'completed' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_created_at ON videos(created_at);

CREATE INDEX IF NOT EXISTS idx_status ON videos(status);

