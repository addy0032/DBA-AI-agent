-- ============================================================
-- SQL SERVER OBSERVABILITY PLATFORM — STRESS TEST SCRIPTS
-- ============================================================
-- Run these in separate SSMS query windows (tabs) against
-- your AdventureWorks2025 database to generate real activity
-- that the dashboard will detect and visualize.
--
-- ⚠️ SAFE FOR DEV/TEST ONLY. DO NOT RUN IN PRODUCTION.
-- ============================================================

-- ============================
-- TEST 1: BLOCKING CHAIN
-- ============================
-- Run this in WINDOW 1 first. It grabs a lock and holds it.
-- Then run TEST 1B in WINDOW 2 to create a blocked session.

-- WINDOW 1 — The Blocker (run this first, leave it open)
USE AdventureWorks2025;
GO

BEGIN TRANSACTION;

-- Lock a row exclusively
UPDATE Person.Person
SET ModifiedDate = GETDATE()
WHERE BusinessEntityID = 1;

-- DO NOT COMMIT — leave this open to hold the lock!
-- The dashboard should show:
--   • Blocked Sessions > 0  (on /dashboard and /workload)
--   • A blocking chain on /workload
--   • Head Blocker count on /dashboard
-- 
-- When done testing, run: ROLLBACK TRANSACTION;
PRINT '>>> Blocker active. Run TEST 1B in another window. <<<';
PRINT '>>> When done, run: ROLLBACK TRANSACTION <<<';
