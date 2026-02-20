-- ============================
-- TEST 4: TEMPDB PRESSURE
-- ============================
-- Run this in WINDOW 5. Creates temp tables and sorts
-- that consume TempDB space.

USE AdventureWorks2025;
GO

-- Fill a large temp table
CREATE TABLE #StressTemp (
    ID INT IDENTITY,
    Col1 NVARCHAR(500),
    Col2 NVARCHAR(500),
    Col3 NVARCHAR(500),
    Col4 NVARCHAR(500)
);

INSERT INTO #StressTemp (Col1, Col2, Col3, Col4)
SELECT TOP 500000
    REPLICATE('A', 200),
    REPLICATE('B', 200),
    REPLICATE('C', 200),
    REPLICATE('D', 200)
FROM sys.all_objects a
CROSS JOIN sys.all_objects b;

-- Force sorts that spill
SELECT * FROM #StressTemp ORDER BY Col1 DESC, Col2 ASC, Col3, Col4;

-- Expected dashboard behavior:
--   /io   → TempDB Used (MB) spikes significantly
--   /waits → WRITELOG and IO_COMPLETION waits may appear
--
-- Cleanup
DROP TABLE IF EXISTS #StressTemp;
PRINT '>>> TempDB stress test complete <<<';
