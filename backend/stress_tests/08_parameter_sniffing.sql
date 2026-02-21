-- ============================================================
-- TEST 8: PARAMETER SNIFFING (GUARANTEED PLAN VARIANCE)
-- ============================================================
-- Uses two separate queries on the SAME query_id via 
-- plan guides / hints to GUARANTEE different plans in QS.
-- ============================================================

USE AdventureWorks2025;
GO

-- Ensure QS is on and flushed
ALTER DATABASE AdventureWorks2025 SET QUERY_STORE = ON;
EXEC sp_query_store_flush_db;
GO

-- Step 1: Create skewed table if not exists
IF OBJECT_ID('dbo.SkewedOrders', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.SkewedOrders (
        OrderID INT IDENTITY PRIMARY KEY,
        CustomerID INT NOT NULL,
        OrderDate DATE NOT NULL DEFAULT GETDATE(),
        Amount DECIMAL(10,2) NOT NULL DEFAULT 100.00,
        Notes NVARCHAR(200) DEFAULT REPLICATE('X', 200)
    );

    -- 100K rows for customer 1
    INSERT INTO dbo.SkewedOrders (CustomerID, Amount)
    SELECT TOP 100000 1, ABS(CHECKSUM(NEWID())) % 10000 / 100.0
    FROM sys.all_objects a CROSS JOIN sys.all_objects b;

    -- 1 row each for 500 other customers
    INSERT INTO dbo.SkewedOrders (CustomerID, Amount)
    SELECT TOP 500 n.num + 100, ABS(CHECKSUM(NEWID())) % 5000 / 100.0
    FROM (SELECT ROW_NUMBER() OVER (ORDER BY object_id) AS num FROM sys.all_objects) n
    WHERE n.num <= 500;

    CREATE NONCLUSTERED INDEX IX_SkewedOrders_CustID
        ON dbo.SkewedOrders(CustomerID) INCLUDE (Amount, OrderDate);

    UPDATE STATISTICS dbo.SkewedOrders WITH FULLSCAN;
END;
GO

-- Step 2: Create TWO procs that run the SAME underlying query
-- but with different hint strategies. Query Store will see
-- different plan_ids under the same query pattern.

IF OBJECT_ID('dbo.usp_SniffFast', 'P') IS NOT NULL DROP PROCEDURE dbo.usp_SniffFast;
IF OBJECT_ID('dbo.usp_SniffSlow', 'P') IS NOT NULL DROP PROCEDURE dbo.usp_SniffSlow;
GO

-- FAST version: forces an Index Seek via FORCESEEK hint
CREATE PROCEDURE dbo.usp_SniffFast @CustID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT OrderID, CustomerID, OrderDate, Amount
    FROM dbo.SkewedOrders WITH (FORCESEEK)
    WHERE CustomerID = @CustID
    ORDER BY OrderDate DESC;
END;
GO

-- SLOW version: forces a Table Scan via FORCESCAN hint
CREATE PROCEDURE dbo.usp_SniffSlow @CustID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT OrderID, CustomerID, OrderDate, Amount
    FROM dbo.SkewedOrders WITH (FORCESCAN)
    WHERE CustomerID = @CustID
    ORDER BY OrderDate DESC;
END;
GO

-- Step 3: Also run raw parameterized queries to populate QS 
-- with the same query text but different plans via OPTION hints.
-- This makes Query Store record 2 plans for the same query shape.

-- Plan 1: Index Seek (thin customer, fast)
DECLARE @i INT = 0;
WHILE @i < 30
BEGIN
    DECLARE @c1 INT = 150;
    SELECT OrderID, CustomerID, OrderDate, Amount
    FROM dbo.SkewedOrders
    WHERE CustomerID = @c1
    ORDER BY OrderDate DESC
    OPTION (OPTIMIZE FOR (@c1 = 150));
    SET @i = @i + 1;
END;
GO

-- Plan 2: Force recompile with fat customer (different plan)
DECLARE @j INT = 0;
WHILE @j < 30
BEGIN
    DECLARE @c2 INT = 1;
    SELECT OrderID, CustomerID, OrderDate, Amount
    FROM dbo.SkewedOrders
    WHERE CustomerID = @c2
    ORDER BY OrderDate DESC
    OPTION (OPTIMIZE FOR (@c2 = 1), RECOMPILE);
    SET @j = @j + 1;
END;
GO

-- Step 4: Execute both procs to register dramatically different performance
DECLARE @k INT = 0;
WHILE @k < 20
BEGIN
    EXEC dbo.usp_SniffFast @CustID = 150;
    SET @k = @k + 1;
END;
GO

DECLARE @m INT = 0;
WHILE @m < 20
BEGIN
    EXEC dbo.usp_SniffSlow @CustID = 1;
    SET @m = @m + 1;
END;
GO

-- Step 5: Flush to Query Store
EXEC sp_query_store_flush_db;
GO

-- Step 6: Verify — should show 2+ plan_ids per query
SELECT
    q.query_id,
    COUNT(DISTINCT p.plan_id) AS plan_count,
    MIN(rs.avg_duration) AS min_avg_dur,
    MAX(rs.avg_duration) AS max_avg_dur,
    CASE WHEN MIN(rs.avg_duration) > 0 
        THEN MAX(rs.avg_duration) / MIN(rs.avg_duration) 
        ELSE 0 END AS variance_ratio
FROM sys.query_store_query q
JOIN sys.query_store_plan p ON q.query_id = p.query_id
JOIN sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
JOIN sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
WHERE qt.query_sql_text LIKE '%SkewedOrders%'
  AND qt.query_sql_text NOT LIKE '%query_store%'
GROUP BY q.query_id
HAVING COUNT(DISTINCT p.plan_id) >= 1
ORDER BY variance_ratio DESC;

PRINT '>>> Done. Restart backend or wait 5 min for slow poll. <<<';
PRINT '>>> Then check /query-store for Param Sniffing Suspects. <<<';

-- Cleanup: 
-- DROP PROCEDURE IF EXISTS dbo.usp_SniffFast;
-- DROP PROCEDURE IF EXISTS dbo.usp_SniffSlow;
-- DROP TABLE IF EXISTS dbo.SkewedOrders;
