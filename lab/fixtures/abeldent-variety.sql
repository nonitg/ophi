-- FAKE recent chart data for the lab VM only (Fictional Data), so the Ophi board in ABELDent mode has cases in every
-- column. Never run against a clinic's database. Fictional Data stops in 2007, so every chart reads as stale today.
-- Adds, per patient below: a 2026-08-20 visit with a periapical of the crown tooth and four bitewings, a certified
-- 6-site perio exam (copied from pid 162's), a clinical note on the tooth, and CDCP coverage (plan 333333 under Sun Life).
-- ZZTEST (pid 168) also gets a planned crown on #46. Every row carries the stamp 2026-08-20 09:00:07 (Notes also
-- MachineName OPHI-FAKE); undo with abeldent-variety-undo.sql, or restore C:\AbelBackups\*.bak.
--
--   Dentist review   6 C.WATSON #16, 60 B.MARTIN #26, 168 ZZTEST #46; 7 L.JONES #22 (Ophi's demo seed signs it: Ready to send)
--   Paperwork        56 PROVOST #26 and 165 MILLER #36 (code 27215 to confirm), 163 GALATIO #16 (plan already applied)
--   Needs patient    9 SMITH #17 (films only: the perio chart is still old); 5, 8, 33, 166 untouched
--   Sun Life         158/160/162/164: fresh charts; their claims are in fake-sunlife-responses.sql
SET XACT_ABORT ON;
BEGIN TRAN;
DECLARE @at datetime = '2026-08-20T09:00:07';

-- Re-running replaces the earlier seed.
DELETE FROM Notes WHERE MachineName = 'OPHI-FAKE';
DELETE FROM Transactions WHERE DatePosted = @at;
DELETE FROM Perio WHERE Date = @at;
DELETE FROM Charts WHERE Date = @at;
DELETE FROM Plans WHERE Date = @at;
DELETE FROM ixi WHERE ixiplanid = 'CDCP';
DELETE FROM nsp WHERE nid = 'CDCP';

DECLARE @t TABLE (pid int, tooth tinyint, perio bit);
INSERT @t VALUES (6, 16, 1), (60, 26, 1), (168, 46, 1), (7, 22, 1), (56, 26, 1), (165, 36, 1), (163, 16, 1), (9, 17, 0),
                 (158, 24, 1), (160, 26, 1), (162, 26, 1), (164, 36, 1);

-- CDCP as a clinic sets it up: a Sun Life plan numbered 333333. The certificate is the client's CDCP number.
INSERT INTO nsp (nid, nplanname, nplnno, ninscoid, ndivsect, noperhandle, nfeeyear, nchargesched, ncopaysched, nspdeductibles,
  nspcarryover, nfeereplace, nnotes, nnots2, nanniv, nspmaximums, nshowcover, nassigned, nformid, niswelfare, nskipstate, nagerule,
  nspexclusive, nspdiagreqd, nspsigreqd, nspplantype, nsppreventive, nspbasic, nspmajor, nsportho, nsporthoage, nsporthostudent,
  nspdefltremainder, nsppercentagelimit)
SELECT 'CDCP', 'Canadian Dental Care Plan', '333333', ninscoid, ndivsect, noperhandle, nfeeyear, nchargesched, ncopaysched, nspdeductibles,
  nspcarryover, nfeereplace, nnotes, nnots2, nanniv, nspmaximums, nshowcover, nassigned, nformid, niswelfare, nskipstate, nagerule,
  nspexclusive, nspdiagreqd, nspsigreqd, nspplantype, nsppreventive, nspbasic, nspmajor, nsportho, nsporthoage, nsporthostudent,
  nspdefltremainder, nsppercentagelimit
FROM nsp WHERE nid = 'SU254221';

INSERT INTO ixi (ixipid, ixiplno, ixiplanid, ixicertno, ixiassigned, ixisubpid, ixireltosub, ixigroupno, ixidivsect, ixifamplan,
  ixideduct, ixileft, ixisubuse, ixicardseqno, ixiReleaseOfInfo, ixiIsActive, ixiIsReplacement)
SELECT t.pid, CASE WHEN EXISTS (SELECT 1 FROM ixi x WHERE x.ixipid = t.pid AND RTRIM(x.ixiplno) = '1') THEN '2' ELSE '1' END,
  'CDCP', CONCAT('5512', RIGHT(CONCAT('00000', t.pid), 5)), 1, 0, 'I', '', '', 0, 0, 0, '', '', ' ', 1, 0
FROM @t t;

-- ZZTEST's planned crown, on a treatment plan of its own.
INSERT INTO Plans (PatID, PlanNum, Date, Descr, State) VALUES (168, 1, @at, 'crn #46', 1);
INSERT INTO Transactions (Date, patID, ChartNum, Grp, ToothNum, ProvID, Code, ChartCode, Descr, Billed, Units, Deleted, PlanNum,
  Phase, Type, Appt, Applied, RespProvID, ItemNum, DatePosted, IsRamq)
VALUES (@at, 168, 0, 0, 46, 'T', '27211', 203, 'Porcelain/Ceramic/Polymer Glass Fused Metal Based Crown', 128500, 0, 0, 1,
  1, 'P', 0, 0, 'T', 0, @at, 0);

-- The recall visit, its films and the note.
INSERT INTO Charts (patID, ChartNum, Date, ChartDesc, EntryDate)
SELECT t.pid, ISNULL((SELECT MAX(c.ChartNum) FROM Charts c WHERE c.patID = t.pid), 0) + 1, @at, 'Recall exam', @at FROM @t t;

INSERT INTO Transactions (Date, patID, ChartNum, Grp, ToothNum, ProvID, Code, ChartCode, Descr, Billed, Units, Deleted, PlanNum,
  Phase, Type, Appt, Applied, RespProvID, ItemNum, DatePosted, IsRamq)
SELECT @at, t.pid, c.ChartNum, 0, f.tooth, 'T', f.code, 242, f.descr, f.fee, 0, 0, 0, 1, ' ', 1, 0, 'T', 0, @at, 0
FROM @t t JOIN Charts c ON c.patID = t.pid AND c.Date = @at
CROSS APPLY (VALUES (t.tooth, '02111', 'Single Periapical Film', 1936), (0, '02144', 'Four Bitewings', 3340)) f(tooth, code, descr, fee);

INSERT INTO Notes (PatID, Date, KeyNumber, KeyType, RefNumber, NoteType, OperatorID, Note, ToothNumber, Colour, MachineName,
  IsDeleted, IsLatest, IsSignedOff)
SELECT t.pid, @at, c.ChartNum, 1, (SELECT MAX(RefNumber) FROM Notes) + ROW_NUMBER() OVER (ORDER BY t.pid), 3, 'T',
  CONCAT('Recall exam. Tooth ', t.tooth, ': large failing restoration with a fractured cusp and recurrent decay under the margin. ',
         'Vital, no periapical pathology on today''s PA. Remaining restorations sound. Plan: PFM crown ', t.tooth, '.'),
  t.tooth, -16777216, 'OPHI-FAKE', 0, 1, 1
FROM @t t JOIN Charts c ON c.patID = t.pid AND c.Date = @at;

-- A certified 6-site perio exam: pid 162's latest Fictional Data exam, re-dated.
INSERT INTO Perio (patID, ExamNum, Date, ProvID, MAG, Mobility, Furcation, Recession, Pocket, Bleeding_Suppuration, Attachment, DateCertified)
SELECT t.pid, ISNULL((SELECT MAX(e.ExamNum) FROM Perio e WHERE e.patID = t.pid), 0) + 1, @at, 'T',
  s.MAG, s.Mobility, s.Furcation, s.Recession, s.Pocket, s.Bleeding_Suppuration, s.Attachment, @at
FROM @t t CROSS JOIN (SELECT * FROM Perio WHERE patID = 162 AND ExamNum = 2) s
WHERE t.perio = 1;

COMMIT;
SELECT t.pid, (SELECT COUNT(*) FROM Transactions x WHERE x.patID = t.pid AND x.DatePosted = @at) AS films_or_plan,
  (SELECT COUNT(*) FROM Perio e WHERE e.patID = t.pid AND e.Date = @at) AS perio,
  (SELECT COUNT(*) FROM Notes n WHERE n.PatID = t.pid AND n.MachineName = 'OPHI-FAKE') AS notes,
  (SELECT RTRIM(ixicertno) FROM ixi x WHERE x.ixipid = t.pid AND x.ixiplanid = 'CDCP') AS cdcp
FROM @t t ORDER BY t.pid;
