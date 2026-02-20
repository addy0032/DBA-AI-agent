-- ============================
-- TEST 3: HEAVY I/O & READS
-- ============================
-- Run this in WINDOW 4. Generates massive logical reads
-- and triggers table scans.

USE AdventureWorks2025;
GO

-- Force table scans with no useful index
-- This shows up in Top Queries by Reads on /workload
SELECT COUNT(*)
FROM Sales.SalesOrderDetail sod
CROSS JOIN Production.TransactionHistory th
WHERE sod.OrderQty > 0 AND th.TransactionType = 'W';
GO

-- Large sort spilling to TempDB
SELECT *
FROM Sales.SalesOrderDetail
ORDER BY NEWID();
GO

-- Repeat to keep I/O sustained
SELECT TOP 0
    a.SalesOrderID,
    b.ProductID,
    CHECKSUM(a.CarrierTrackingNumber, b.ReferenceOrderID) AS chk
FROM Sales.SalesOrderDetail a
CROSS JOIN Production.TransactionHistory b;
GO

-- Expected dashboard behavior:
--   /workload   → Top Queries by Reads shows massive read count
--   /io         → File read/write latency may increase
--                  TempDB usage may spike (from sorts)
--   /waits      → PAGEIOLATCH_*, IO_COMPLETION waits appear
--   /server     → Buffer Cache Hit Ratio may dip slightly
--
PRINT '>>> I/O stress test complete <<<';
