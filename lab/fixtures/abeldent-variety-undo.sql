-- Remove the fake recent chart data written by abeldent-variety.sql.
SET XACT_ABORT ON;
BEGIN TRAN;
DECLARE @at datetime = '2026-08-20T09:00:07';
DELETE FROM Notes WHERE MachineName = 'OPHI-FAKE';
DELETE FROM Transactions WHERE DatePosted = @at;
DELETE FROM Perio WHERE Date = @at;
DELETE FROM Charts WHERE Date = @at;
DELETE FROM Plans WHERE Date = @at;
DELETE FROM ixi WHERE ixiplanid = 'CDCP';
DELETE FROM nsp WHERE nid = 'CDCP';
COMMIT;
SELECT (SELECT COUNT(*) FROM Transactions WHERE DatePosted = @at) + (SELECT COUNT(*) FROM Perio WHERE Date = @at) AS rows_left;
