-- ============================================================================
-- Scraper Health Monitoring Schema Extension
-- Adds tables and functions for tracking scraper health metrics
-- ============================================================================

-- Scraper Health Metrics: Track scraper performance and errors
CREATE TABLE IF NOT EXISTS scraper_health_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(50) NOT NULL,  -- twitter, youtube, reddit, web
    scrape_attempt_id UUID,  -- Reference to scrape_jobs.id if applicable
    status VARCHAR(20) NOT NULL,  -- success, error, rate_limited, timeout
    error_type VARCHAR(50),  -- http_error, rate_limit, timeout, parse_error, auth_error
    error_message TEXT,
    http_status_code INTEGER,
    response_time_ms INTEGER,  -- Response time in milliseconds
    items_scraped INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb  -- Additional context
);

-- Scraper Uptime Tracking: Track last successful scrape per platform
CREATE TABLE IF NOT EXISTS scraper_uptime (
    platform VARCHAR(50) PRIMARY KEY,
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,
    total_attempts INTEGER DEFAULT 0,
    total_successes INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    uptime_percentage FLOAT DEFAULT 100.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize uptime tracking for all platforms
INSERT INTO scraper_uptime (platform) VALUES
    ('twitter'),
    ('youtube'),
    ('reddit'),
    ('web')
ON CONFLICT (platform) DO NOTHING;

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_health_metrics_platform ON scraper_health_metrics(platform);
CREATE INDEX IF NOT EXISTS idx_health_metrics_status ON scraper_health_metrics(status);
CREATE INDEX IF NOT EXISTS idx_health_metrics_timestamp ON scraper_health_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_health_metrics_error_type ON scraper_health_metrics(error_type);

-- ============================================================================
-- Functions for Health Monitoring
-- ============================================================================

-- Function: Get success rate by platform
CREATE OR REPLACE FUNCTION get_success_rate_by_platform(
    target_platform VARCHAR(50),
    time_window_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
    platform VARCHAR(50),
    total_attempts BIGINT,
    successful_attempts BIGINT,
    failed_attempts BIGINT,
    success_rate FLOAT,
    avg_response_time_ms FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        shm.platform,
        COUNT(*) AS total_attempts,
        COUNT(*) FILTER (WHERE shm.status = 'success') AS successful_attempts,
        COUNT(*) FILTER (WHERE shm.status != 'success') AS failed_attempts,
        (COUNT(*) FILTER (WHERE shm.status = 'success')::FLOAT / NULLIF(COUNT(*), 0) * 100) AS success_rate,
        AVG(shm.response_time_ms) AS avg_response_time_ms
    FROM scraper_health_metrics shm
    WHERE shm.platform = target_platform
        AND shm.timestamp > CURRENT_TIMESTAMP - (time_window_hours || ' hours')::INTERVAL
    GROUP BY shm.platform;
END;
$$ LANGUAGE plpgsql;

-- Function: Get error breakdown by platform
CREATE OR REPLACE FUNCTION get_error_breakdown_by_platform(
    target_platform VARCHAR(50),
    time_window_hours INTEGER DEFAULT 24
)
RETURNS TABLE (
    error_type VARCHAR(50),
    error_count BIGINT,
    percentage FLOAT,
    latest_occurrence TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        shm.error_type,
        COUNT(*) AS error_count,
        (COUNT(*)::FLOAT / NULLIF(SUM(COUNT(*)) OVER (), 0) * 100) AS percentage,
        MAX(shm.timestamp) AS latest_occurrence
    FROM scraper_health_metrics shm
    WHERE shm.platform = target_platform
        AND shm.status != 'success'
        AND shm.error_type IS NOT NULL
        AND shm.timestamp > CURRENT_TIMESTAMP - (time_window_hours || ' hours')::INTERVAL
    GROUP BY shm.error_type
    ORDER BY error_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function: Get overall health dashboard
CREATE OR REPLACE FUNCTION get_health_dashboard()
RETURNS TABLE (
    platform VARCHAR(50),
    status VARCHAR(20),
    success_rate FLOAT,
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    consecutive_failures INTEGER,
    uptime_percentage FLOAT,
    avg_response_time_ms FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        su.platform,
        CASE
            WHEN su.consecutive_failures >= 5 THEN 'critical'
            WHEN su.consecutive_failures >= 3 THEN 'warning'
            WHEN su.success_rate < 80.0 THEN 'degraded'
            ELSE 'healthy'
        END AS status,
        (su.total_successes::FLOAT / NULLIF(su.total_attempts, 0) * 100) AS success_rate,
        su.last_success_at,
        su.last_failure_at,
        su.consecutive_failures,
        su.uptime_percentage,
        (
            SELECT AVG(response_time_ms)
            FROM scraper_health_metrics
            WHERE platform = su.platform
                AND timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
        ) AS avg_response_time_ms
    FROM scraper_uptime su
    ORDER BY su.platform;
END;
$$ LANGUAGE plpgsql;

-- Function: Record scraper attempt
CREATE OR REPLACE FUNCTION record_scraper_attempt(
    p_platform VARCHAR(50),
    p_status VARCHAR(20),
    p_error_type VARCHAR(50) DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_http_status_code INTEGER DEFAULT NULL,
    p_response_time_ms INTEGER DEFAULT NULL,
    p_items_scraped INTEGER DEFAULT 0,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    metric_id UUID;
BEGIN
    -- Insert health metric
    INSERT INTO scraper_health_metrics (
        platform, status, error_type, error_message, http_status_code,
        response_time_ms, items_scraped, metadata
    )
    VALUES (
        p_platform, p_status, p_error_type, p_error_message, p_http_status_code,
        p_response_time_ms, p_items_scraped, p_metadata
    )
    RETURNING id INTO metric_id;

    -- Update uptime tracking
    UPDATE scraper_uptime
    SET
        total_attempts = total_attempts + 1,
        total_successes = CASE WHEN p_status = 'success' THEN total_successes + 1 ELSE total_successes END,
        total_failures = CASE WHEN p_status != 'success' THEN total_failures + 1 ELSE total_failures END,
        last_success_at = CASE WHEN p_status = 'success' THEN CURRENT_TIMESTAMP ELSE last_success_at END,
        last_failure_at = CASE WHEN p_status != 'success' THEN CURRENT_TIMESTAMP ELSE last_failure_at END,
        consecutive_failures = CASE
            WHEN p_status = 'success' THEN 0
            ELSE consecutive_failures + 1
        END,
        uptime_percentage = (
            CASE WHEN p_status = 'success' THEN total_successes + 1 ELSE total_successes END::FLOAT /
            NULLIF((total_attempts + 1), 0) * 100
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE platform = p_platform;

    RETURN metric_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers
-- ============================================================================

CREATE TRIGGER update_scraper_uptime_updated_at
    BEFORE UPDATE ON scraper_uptime
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify tables created
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('scraper_health_metrics', 'scraper_uptime')
ORDER BY tablename;

-- Verify initial uptime data
SELECT * FROM scraper_uptime ORDER BY platform;
