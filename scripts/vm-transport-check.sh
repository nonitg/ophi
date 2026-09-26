#!/usr/bin/env bash
# Live check of lab/vm/vm + q.ps1 against the ABELDent VM: transport primitives, SQL rails,
# param binding, ISO dates, UTF-8. Read-only.
set -uo pipefail
cd "$(dirname "$0")/.."
VM=./lab/vm/vm
step() { printf '\n== %s\n' "$1"; }

step status;            $VM status
step sync;              $VM sync
step exec;              $VM exec 'whoami; $PSVersionTable.PSVersion.ToString()'
step "sql table";       $VM sql "SELECT TOP 3 pid, plname, pbirth FROM pat ORDER BY pid" '' table
step "sql json + ISO";  $VM sql "SELECT TOP 2 pid, pbirth, NULL AS nothing FROM pat ORDER BY pid" '' json
step "params bind";     $VM sql "SELECT pid, plname FROM pat WHERE pid = @pid AND plname LIKE @q + '%'" '' json '{"pid": 5, "q": ""}'
step "injection inert"; $VM sql "SELECT COUNT(*) AS n FROM pat WHERE plname = @q" '' json "{\"q\": \"x'; DROP TABLE pat;--\"}"
step "UTF-8";           $VM sql "SELECT N'Gagné Côté' AS name" '' json
step "0 and 1 rows";    $VM sql "SELECT pid FROM pat WHERE pid = -1" '' json; $VM sql "SELECT 1 AS one" '' json
step "write refused";   $VM sql "UPDATE pat SET plname = plname WHERE pid = -1" '' json; echo "exit=$?"
step "bad SQL errors";  $VM sql "SELECT nope FROM pat" '' json; echo "exit=$?"
step "long query (>8191 chars, over stdin)"
long="SELECT COUNT(*) AS n FROM pat WHERE pid IN ($(seq -s, 1 5000))"
echo "query bytes: ${#long}"; $VM sql "$long" '' json
