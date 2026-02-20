-- ============================
-- TEST 1B: BLOCKED VICTIM
-- ============================
-- Run this in WINDOW 2, AFTER running 01_blocker.sql in Window 1.
-- This query will hang because it's waiting for the lock.

USE AdventureWorks2025;
GO

-- This will be BLOCKED by Window 1's open transaction
UPDATE Person.Person
SET ModifiedDate = GETDATE()
WHERE BusinessEntityID = 1;

-- Expected dashboard behavior:
--   /dashboard  → "Blocked" KPI card turns RED with value ≥ 1
--   /workload   → Blocking Chains table shows the chain
--                  Head Blocker count ≥ 1
--   Wait Stats  → LCK_M_U or LCK_M_X wait type appears
--
-- This query will stay stuck until you ROLLBACK in Window 1.
PRINT 'This line will only print after the blocker releases.';
