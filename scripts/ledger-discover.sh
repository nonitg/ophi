#!/bin/bash
# Read-only discovery queries against the ABELDent clinical ledger (Transactions) for the
# chart_dump rewrite. Each `vm sql` call is lock-serialised (~3-6 s while the UI agent works).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
q() { echo "--- $1"; ./lab/vm/vm sql "$2" '' json; echo; }
q "Type values" "SELECT Type, COUNT(*) n, SUM(CASE WHEN Deleted=0 THEN 1 ELSE 0 END) live FROM Transactions GROUP BY Type"
q "Deleted values" "SELECT Deleted, COUNT(*) n FROM Transactions GROUP BY Deleted"
q "Default pids" "SELECT COUNT(DISTINCT patID) n FROM Transactions WHERE Type='P' AND Deleted=0"
q "Condition chart codes" "SELECT ChartCode, MIN(Descr) Descr, COUNT(*) n FROM Transactions WHERE Code IS NULL OR Code='' GROUP BY ChartCode ORDER BY ChartCode"
q "Plans.State values" "SELECT State, COUNT(*) n FROM Plans GROUP BY State"
q "Planned without tooth" "SELECT patID, TransID, Code, ToothNum FROM Transactions WHERE Type='P' AND Deleted=0 AND (ToothNum IS NULL OR ToothNum=0)"
q "Sample rows pid 60" "SELECT TransID, CONVERT(varchar(10),Date,23) Date, patID, ChartNum, Grp, ToothNum, ProvID, Code, ChartCode, Extra, Descr, Billed, Units, Surfaces, Deleted, PlanNum, MatID, Phase, Type, Appt, Applied, RespProvID, ItemNum, CONVERT(varchar(10),DatePosted,23) DatePosted, Identifier, Modifier, GroupAssociation, IsRamq, EnteredUser, ResponsibleUser, ConsentRecordId, State FROM Transactions WHERE patID=60 AND Type='P'"
