-- Rollback Migration: Remove ultra_learning table
-- Date: 2025-11-22

DROP TRIGGER IF EXISTS update_ultra_learning_updated_at ON ultra_learning;
DROP TABLE IF EXISTS ultra_learning CASCADE;
