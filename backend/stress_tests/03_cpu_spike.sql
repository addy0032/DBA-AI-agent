-- ============================
-- TEST 2: CPU SPIKE
-- ============================
-- Run this in WINDOW 3. It generates heavy CPU load via
-- expensive cross joins and calculations.

USE AdventureWorks2025;
GO

-- Burn CPU for ~30-60 seconds with expensive computation
-- This generates massive worker time in dm_exec_query_stats
DECLARE @i INT = 0;
WHILE @i < 5
BEGIN
    SELECT TOP 0
        a.BusinessEntityID,
        CHECKSUM(a.FirstName, b.LastName, c.FirstName) AS hash_val,
        POWER(CAST(a.BusinessEntityID AS FLOAT), 1.5) AS power_calc,
        LOG(ABS(a.BusinessEntityID) + 1) * LOG(ABS(b.BusinessEntityID) + 1) AS log_product
    FROM Person.Person a
    CROSS JOIN Person.Person b
    CROSS JOIN (SELECT TOP 50 * FROM Person.Person) c
    WHERE a.BusinessEntityID % 7 = 0;

    SET @i = @i + 1;
END;

-- Expected dashboard behavior:
--   /dashboard  → SQL CPU jumps to 40-90%+
--   /server     → SQL CPU Usage turns amber/red
--                  Runnable Tasks increases
--                  Signal Wait % may increase
--   /workload   → Top Queries by CPU shows this hash
--   CPU Trend sparkline on /dashboard shows a spike
--
PRINT '>>> CPU stress test complete <<<';
