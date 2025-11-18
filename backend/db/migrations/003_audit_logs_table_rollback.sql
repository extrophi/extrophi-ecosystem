-- Rollback Migration: 003 - Audit Logs Table
-- Description: Remove audit logs table
-- Date: 2025-11-18
-- Author: BETA-2 Agent

-- ============================================================================
-- ROLLBACK: DROP AUDIT LOGS TABLE
-- ============================================================================

-- Drop the cleanup function
DROP FUNCTION IF EXISTS cleanup_old_audit_logs(INTEGER);

-- Drop all indices
DROP INDEX IF EXISTS idx_audit_logs_endpoint_status;
DROP INDEX IF EXISTS idx_audit_logs_status_created;
DROP INDEX IF EXISTS idx_audit_logs_endpoint_created;
DROP INDEX IF EXISTS idx_audit_logs_user_created;
DROP INDEX IF EXISTS idx_audit_logs_created_at;
DROP INDEX IF EXISTS idx_audit_logs_client_ip;
DROP INDEX IF EXISTS idx_audit_logs_response_status;
DROP INDEX IF EXISTS idx_audit_logs_api_key_id;
DROP INDEX IF EXISTS idx_audit_logs_user_id;
DROP INDEX IF EXISTS idx_audit_logs_method;
DROP INDEX IF EXISTS idx_audit_logs_endpoint;

-- Drop the audit_logs table
DROP TABLE IF EXISTS audit_logs CASCADE;
