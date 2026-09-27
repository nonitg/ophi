-- FAKE Sun Life predetermination responses for the lab VM only (Fictional Data), so Ophi can be demoed
-- reading a decision out of ABELDent. Never run against a clinic's database.
-- Every row is tagged OPHI-FAKE and uses ClaimID 9001-9099 / LogEventID 9101-9199; undo with
-- fake-sunlife-responses-undo.sql or restore C:\AbelBackups\*_before_fake_sunlife.bak.
--
-- The CDAnet message bodies are NOT real CDAnet wire format (the layout is not public). They are
-- field=value pairs keyed by ABELDent's own CDADataDictionary ids (G05, G15, G26...), so a reader
-- can be written against the fields now and swapped for a real parser once a real response exists.
--
--   158 YOKOYAMA #24  Status P  EOB back: DENIED, periapical radiograph missing
--   162 RANDAL   #26  Status P  EOB back: APPROVED
--   160 CHERSKI  #26  Status Q  sent, Sun Life will answer by paper (letter-upload demo)
--   164 GOERTSEN #36  Status S  sent 2026-09-22, Sun Life still reviewing
-- Coverage is the lab's CDCP plan (plan 333333) from abeldent-variety.sql; run that first.
SET XACT_ABORT ON;
BEGIN TRAN;

DELETE FROM ClaimResult WHERE ClaimID BETWEEN 9001 AND 9099;
DELETE FROM ClaimItem   WHERE ClaimID BETWEEN 9001 AND 9099;
DELETE FROM Claim       WHERE ClaimID BETWEEN 9001 AND 9099;
DELETE FROM NetLog      WHERE LogEventID BETWEEN 9101 AND 9199;

INSERT INTO Claim (ClaimID, Timestamp, NetworkID, OfficeNumber, OfficeSequenceNumber, FormID, ResponsibleProviderID,
                   PatientID, ServiceDate, BillingDate, PatientPlanNumber, PlanID, CarrierID, CarrierClaimNumber,
                   SubscriberID, RelationshipToSubscriber, PolicyNumber, DivisionSection, CertificateNumber, Status,
                   LogEventID, NetCarrierNumber, IsPredetermination, SubmissionType)
VALUES
 (9001, '2026-09-10T10:02:00', 'ICA', '0', 9001, 'OPHI-FAKE', 'T', 158, '2026-10-06', '2026-09-10', '2', 'CDCP', 'SUNLIFE', 'SL260910000158', 158, 'I', '333333', '', '551200158', 'P', 9102, '16', 1, 0),
 (9002, '2026-09-08T14:30:00', 'ICA', '0', 9002, 'OPHI-FAKE', 'T', 162, '2026-10-01', '2026-09-08', '2', 'CDCP', 'SUNLIFE', 'SL260908000162', 162, 'I', '333333', '', '551200162', 'P', 9104, '16', 1, 0),
 (9003, '2026-09-15T09:15:00', 'ICA', '0', 9003, 'OPHI-FAKE', 'T', 160, '2026-10-14', '2026-09-15', '2', 'CDCP', 'SUNLIFE', 'SL260915000160', 160, 'I', '333333', '', '551200160', 'Q', 9105, '16', 1, 0),
 (9004, '2026-09-22T11:40:00', 'ICA', '0', 9004, 'OPHI-FAKE', 'T', 164, '2026-10-20', '2026-09-22', '2', 'CDCP', 'SUNLIFE', 'SL260922000164', 164, 'I', '333333', '', '551200164', 'S', 9106, '16', 1, 0);

-- ServiceTransaction = the planned crown's Transactions.TransID
INSERT INTO ClaimItem (ClaimID, ClaimItemNumber, ClaimLineNumber, OnOtherLine, ServiceTransaction, ServiceItemNumber, InsuranceTransaction, Amount, ServiceDate)
VALUES
 (9001, 1, 1, 0, 1178, 1, 0, 845.00, '2026-10-06'),
 (9002, 1, 1, 0, 1049, 1, 0, 581.00, '2026-10-01'),
 (9003, 1, 1, 0, 1107, 1, 0, 581.00, '2026-10-14'),
 (9004, 1, 1, 0, 700, 1, 0, 629.45, '2026-10-20');

INSERT INTO ClaimResult (ClaimID, LogEventID, ResultType, WasEmbedded)
VALUES (9001, 9102, 'P', 0), (9002, 9104, 'P', 0), (9003, 9105, 'Q', 0), (9004, 9106, 'S', 0);

INSERT INTO NetLog (LogEventID, Timestamp, Workstation, UserName, SubmittingOfficeNumber, FormatVersionNumber, NetTransactionCode,
                    CarrierIDNumber, SentMessage, ReceivedMessage, Errors, NetworkID, Gateway, xClaimID, xResultType, xOfficeSequenceNumber)
VALUES
 -- 158: predetermination sent (03) and acknowledged, then the deferred Predetermination EOB (23) with a denial
 (9101, '2026-09-10T10:02:00', 'OPHI-FAKE', 'ophi-fake', '0', '04', '03', '16',
  'A04=03|F07-1=27211|F08-1=24|F12-1=84500',
  'A04=13|G05=A|G07=Predetermination received. Response to follow.', '', 'ICA', 'FAKE', 9001, 'S', '9001'),
 (9102, '2026-09-17T08:40:00', 'OPHI-FAKE', 'ophi-fake', '0', '04', '23', '16', '',
  'A04=23|G01=SL260910000158|G05=E|G04=84500|G28=0|G18-1=1|F07-1=27211|G12-1=0|G15-1=0|G16-1=01|G11=2|G45-1=01|G26-1=Predetermination not approved. A current periapical radiograph|G45-2=01|G26-2=of tooth 24 was not received. Resubmit with the radiograph.',
  '', 'ICA', 'FAKE', 9001, 'P', '9001'),
 -- 162: predetermination sent and the Predetermination EOB (23) approves the full insurer portion
 (9103, '2026-09-08T14:30:00', 'OPHI-FAKE', 'ophi-fake', '0', '04', '03', '16',
  'A04=03|F07-1=27211|F08-1=26|F12-1=58100',
  'A04=13|G05=A|G07=Predetermination received. Response to follow.', '', 'ICA', 'FAKE', 9002, 'S', '9002'),
 (9104, '2026-09-15T11:05:00', 'OPHI-FAKE', 'ophi-fake', '0', '04', '23', '16', '',
  'A04=23|G01=SL260908000162|G05=E|G04=58100|G28=29050|G18-1=1|F07-1=27211|G12-1=58100|G14-1=050|G15-1=29050|G11=1|G45-1=01|G26-1=Predetermination approved. Valid for 12 months from this date.',
  '', 'ICA', 'FAKE', 9002, 'P', '9002'),
 -- 160: acknowledged; Sun Life will answer on paper, so no EOB ever reaches ABELDent
 (9105, '2026-09-15T09:15:00', 'OPHI-FAKE', 'ophi-fake', '0', '04', '03', '16',
  'A04=03|F07-1=27211|F08-1=26|F12-1=58100',
  'A04=13|G05=H|G07=Predetermination held for review. Response will be mailed to the office.', '', 'ICA', 'FAKE', 9003, 'Q', '9003'),
 -- 164: acknowledged; Sun Life is reviewing, and its answer will come back through the network
 (9106, '2026-09-22T11:40:00', 'OPHI-FAKE', 'ophi-fake', '0', '04', '03', '16',
  'A04=03|F07-1=27215|F08-1=36|F12-1=62945',
  'A04=13|G05=A|G07=Predetermination received. Response to follow.', '', 'ICA', 'FAKE', 9004, 'S', '9004');

COMMIT;
SELECT c.ClaimID, c.PatientID, c.Status, c.CarrierClaimNumber, n.NetTransactionCode, n.ReceivedMessage
FROM Claim c JOIN NetLog n ON n.LogEventID = c.LogEventID WHERE c.ClaimID BETWEEN 9001 AND 9099 ORDER BY c.ClaimID;
