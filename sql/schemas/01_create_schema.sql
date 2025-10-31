-- =========================================
-- Retention Intelligence System (RIS)
-- Schema Creation Script
-- =========================================

-- Create schema
CREATE SCHEMA IF NOT EXISTS ris;

-- Set search path
SET search_path TO ris, public;

-- Add comments
COMMENT ON SCHEMA ris IS 'Retention Intelligence System - витрины данных для прогнозирования оттока клиентов Hero Journey';
