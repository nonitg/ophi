# Read-only SQL query runner for the lab VM. Lives in C:\ophi on the guest.
# Deliberately mirrors the plan's ReadOnlySqlExecutor rule: the lab tooling refuses to write
# to the vendor database, so the safety rail gets exercised before the real agent exists.
# -AllowWrite is for seeding lab test data only; -DryRun runs a write then rolls it back.
# Query and named params (JSON object) arrive base64 UTF-8 so they survive ssh/cmd quoting.
param(
    [Parameter(Mandatory = $true)][string]$QueryB64,
    [string]$Server = '',
    [string]$Database = 'master',
    [int]$Timeout = 120,
    [ValidateSet('json', 'csv', 'table')][string]$As = 'json',
    [string]$ParamsB64 = '',
    [switch]$AllowWrite,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# Patient names carry accents (French-Canadian); the console's default code page would mangle them
[Console]::OutputEncoding = [Text.Encoding]::UTF8
# 'file:<path>' reads the base64 from a file the host pushed (queries too long for a command line)
if ($QueryB64 -like 'file:*') {
    $qf = $QueryB64.Substring(5)
    $QueryB64 = (Get-Content -Raw $qf).Trim()
    Remove-Item $qf
}
$Query = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($QueryB64))

if (-not ($AllowWrite -or $DryRun)) {
    # Rail 1: no write/DDL/proc keyword anywhere in the text once string literals and comments are
    # removed. Word boundaries keep column names like Deleted or DatePosted legal. INTO blocks
    # SELECT ... INTO; WITH-prefixed DML and leading comments no longer slip past a line-start check.
    $bare = $Query -replace "'([^']|'')*'", "''" -replace '/\*[\s\S]*?\*/', ' ' -replace '--[^\r\n]*', ' '
    $forbidden = '\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|GRANT|REVOKE|BACKUP|RESTORE|EXEC|EXECUTE|INTO|OPENROWSET|OPENQUERY|BULK|DBCC|KILL|SHUTDOWN|WRITETEXT|UPDATETEXT|ENABLE|DISABLE)\b|\b(sp_|xp_)\w+'
    if ($bare -match "(?i)$forbidden") {
        throw "REFUSED: query contains '$($Matches[0])'. Re-run with -AllowWrite if that is genuinely intended."
    }
}

# ABELDent's own config is the source of truth for both instance and database name —
# the database name carries a build timestamp, so hard-coding it would rot on reinstall.
if (-not $Database) { $Database = 'master' }
if (-not $Server -or $Database -eq 'master') {
    $cfg = 'C:\ABELDent\localConfiguration.config'
    if (Test-Path $cfg) {
        $conn = ([xml](Get-Content $cfg -Raw)).localConfiguration.dbConnection
        if (-not $Server -and $conn -match 'Data Source=([^;]+)') { $Server = $Matches[1] }
        if ($Database -eq 'master' -and $conn -match 'Initial Catalog=([^;]+)') { $Database = $Matches[1] }
    }
}
if (-not $Server) { throw 'No SQL Server instance found and none given.' }

# This lab VM is ARM64 Windows. LocalDB ships only an x64 SQLUserInstance.dll, which an
# ARM64 PowerShell cannot load ("error 56"), so the (localdb)\X moniker never resolves.
# Connecting straight to the instance's named pipe skips that shim entirely.
# The pipe name is regenerated on every instance restart, so resolve it each call.
if ($Server -match '^\(localdb\)\\(.+)$') {
    $inst = $Matches[1]
    $sqllocaldb = Get-ChildItem "$env:ProgramFiles\Microsoft SQL Server\*\Tools\Binn\SqlLocalDB.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $sqllocaldb) { throw 'SqlLocalDB.exe not found — cannot resolve the LocalDB pipe.' }
    # LocalDB stops itself a few minutes after the last connection closes (i.e. whenever ABELDent
    # is not running). Starting it is a read-only act on the data and is what ABELDent itself does.
    $pipe = $null
    foreach ($attempt in 1..2) {
        $info = & $sqllocaldb.FullName info $inst 2>&1
        $m = $info | Select-String 'Instance pipe name:\s*(\S+)'
        if ($m) { $pipe = $m.Matches[0].Groups[1].Value; break }
        if ($attempt -eq 1) { & $sqllocaldb.FullName start $inst | Out-Null; Start-Sleep -Seconds 3 }
    }
    if (-not $pipe) { throw "LocalDB instance '$inst' is not running and could not be started: $($info -join ' ')" }
    $Server = $pipe
}

$cs = "Server=$Server;Database=$Database;Integrated Security=SSPI;TrustServerCertificate=True;Connect Timeout=15;Application Name=OphiProbe"
$cn = New-Object System.Data.SqlClient.SqlConnection $cs
$cn.Open()
# Rail 2: everything runs inside a transaction that is always rolled back, so even a query that
# slips past rail 1 leaves the vendor database exactly as it was.
$tx = if ($AllowWrite -and -not $DryRun) { $null } else { $cn.BeginTransaction() }
try {
    $cmd = $cn.CreateCommand()
    $cmd.Transaction = $tx
    $cmd.CommandText = $Query
    $cmd.CommandTimeout = $Timeout
    # Values bind as @name parameters, never spliced into SQL text
    if ($ParamsB64) {
        $params = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($ParamsB64)) | ConvertFrom-Json
        foreach ($p in $params.PSObject.Properties) {
            $v = if ($null -eq $p.Value) { [DBNull]::Value } else { $p.Value }
            [void]$cmd.Parameters.AddWithValue("@$($p.Name)", $v)
        }
    }
    $da = New-Object System.Data.SqlClient.SqlDataAdapter $cmd
    $ds = New-Object System.Data.DataSet
    [void]$da.Fill($ds)

    foreach ($dt in $ds.Tables) {
        # Dates as zone-less ISO: ABELDent stores wall-clock times, and ConvertTo-Json would emit
        # /Date(ms)/ shifted by the VM's zone
        $cols = $dt.Columns.ColumnName
        $rows = foreach ($r in $dt.Rows) {
            $o = [ordered]@{}
            foreach ($c in $cols) {
                $v = $r[$c]
                $o[$c] = if ($v -is [DBNull]) { $null } elseif ($v -is [datetime]) { $v.ToString('yyyy-MM-ddTHH:mm:ss') } else { $v }
            }
            [pscustomobject]$o
        }
        switch ($As) {
            # -InputObject @() keeps the result an array even for 0 or 1 rows; piping would
            # unroll it into a bare object (1 row) or a {value,Count} wrapper (N rows).
            'json'  { if ($null -eq $rows) { '[]' } else { ConvertTo-Json -InputObject @($rows) -Depth 5 -Compress } }
            'csv'   { $rows | ConvertTo-Csv -NoTypeInformation }
            'table' { $rows | Format-Table -AutoSize | Out-String -Width 400 }
        }
    }
}
# A failed batch can already have rolled the transaction back server-side (Connection goes null)
finally { if ($tx -and $tx.Connection) { $tx.Rollback() }; $cn.Close() }
