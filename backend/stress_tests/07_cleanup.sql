-- ============================================================
-- CLEANUP / RESET
-- ============================================================
-- Run this after you're done testing to release all locks
-- and clean up temp objects.

-- Release any open transactions (run in ALL windows)
IF @@TRANCOUNT > 0
    ROLLBACK TRANSACTION;
GO

-- Clean up temp tables
DROP TABLE IF EXISTS #StressTemp;
GO

PRINT '>>> All stress tests cleaned up <<<';
