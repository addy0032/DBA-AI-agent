-- ============================
-- TEST 5: MULTIPLE SESSIONS
-- ============================
-- Run this in WINDOW 6. Creates multiple concurrent sessions
-- in a loop to spike session counts.

USE AdventureWorks2025;
GO

-- Simulate many active queries running simultaneously
-- Each iteration does a moderately expensive query
DECLARE @i INT = 0;
WHILE @i < 20
BEGIN
    -- Each iteration runs a query that takes ~1-2 seconds
    SELECT TOP 1000
        p.BusinessEntityID,
        p.FirstName,
        p.LastName,
        e.JobTitle,
        a.City
    FROM Person.Person p
    LEFT JOIN HumanResources.Employee e ON p.BusinessEntityID = e.BusinessEntityID
    LEFT JOIN Person.BusinessEntityAddress bea ON p.BusinessEntityID = bea.BusinessEntityID
    LEFT JOIN Person.Address a ON bea.AddressID = a.AddressID
    ORDER BY NEWID();  -- Force expensive sort

    -- Small delay
    WAITFOR DELAY '00:00:01';
    SET @i = @i + 1;
END;

-- Expected dashboard behavior:
--   /dashboard  → Active Sessions fluctuates
--   /workload   → Active session count goes up
--                  Sleeping session count increases too
--   /server     → Workers count increases
--
PRINT '>>> Session load test complete <<<';
