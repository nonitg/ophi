#!/bin/bash
# Read-only checks for chart_dump's tdi mirror matching and bridge grouping semantics.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
q() { echo "--- $1"; ./lab/vm/vm sql "$2" '' json; echo; }
q "Completed mirror hit rates by key" "SELECT COUNT(*) n,
 SUM(CASE WHEN EXISTS(SELECT 1 FROM tdi t WHERE t.ipid=x.patID AND t.ijcode=x.Code AND t.itooth=x.ToothNum AND t.itype='' AND t.idate=x.Date) THEN 1 ELSE 0 END) by_date,
 SUM(CASE WHEN EXISTS(SELECT 1 FROM tdi t WHERE t.ipid=x.patID AND t.ijcode=x.Code AND t.itooth=x.ToothNum AND t.itype='' AND t.idate=x.DatePosted) THEN 1 ELSE 0 END) by_dateposted,
 SUM(CASE WHEN EXISTS(SELECT 1 FROM tdi t WHERE t.ipid=x.patID AND t.ijcode=x.Code AND t.itooth=x.ToothNum AND t.itype='') THEN 1 ELSE 0 END) any_date,
 SUM(CASE WHEN EXISTS(SELECT 1 FROM tdi t WHERE t.ipid=x.patID AND t.ijcode=x.Code AND t.itype='') THEN 1 ELSE 0 END) code_only
 FROM Transactions x WHERE x.Type=' ' AND x.Code<>'' AND x.Deleted=0"
q "Unmirrored completed sample pid 8" "SELECT x.TransID, CONVERT(varchar(10),x.Date,23) Date, CONVERT(varchar(10),x.DatePosted,23) Posted, x.Code, x.ToothNum, x.Billed, x.ChartNum FROM Transactions x WHERE x.patID=8 AND x.Type=' ' AND x.Code<>''"
q "tdi pid 8" "SELECT itrid, CONVERT(varchar(10),idate,23) idate, ijcode, itooth, iefee, itype FROM tdi WHERE ipid=8"
q "Grp repeats within patient" "SELECT patID, Grp, COUNT(*) n FROM Transactions WHERE Grp>0 GROUP BY patID, Grp HAVING COUNT(*)>1"
q "Bridge rows Grp vs GroupAssociation" "SELECT patID, TransID, Code, ToothNum, Grp, GroupAssociation, Type FROM Transactions WHERE ChartCode IN (221,254) ORDER BY patID, TransID"
