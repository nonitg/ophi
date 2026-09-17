# Read-only SQL query runner for the lab VM. Lives in C:\colombus on the guest.
# Deliberately mirrors the plan's ReadOnlySqlExecutor rule: the lab tooling refuses to write
# to the vendor database, so the safety rail gets exercised before the real agent exists.
param(
    [Parameter(Mandatory = $true)][string]$Query,
    [string]$Server = '',
    [string]$Database = 'master',
    [int]$Timeout = 120,
    [ValidateSet('json', 'csv', 'table')][string]$As = 'json',
    [switch]$AllowWrite
)

$ErrorActionPreference = 'Stop'

if (-not $AllowWrite) {
    $forbidden = 'INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|GRANT|REVOKE|BACKUP|RESTORE|EXEC\b|EXECUTE\b|sp_|xp_'
    if ($Query -match "(?im)^\s*($forbidden)" -or $Query -match "(?im);\s*($forbidden)") {
        throw "REFUSED: query looks like a write or a proc call. Re-run with -AllowWrite if that is genuinely intended."
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
    $info = & $sqllocaldb.FullName info $inst
    $pipe = ($info | Select-String 'Instance pipe name:\s*(\S+)').Matches.Groups[1].Value
    if (-not $pipe) { throw "LocalDB instance '$inst' is not running (start ABELDent, or: SqlLocalDB start $inst)." }
    $Server = $pipe
}

$cs = "Server=$Server;Database=$Database;Integrated Security=SSPI;TrustServerCertificate=True;Connect Timeout=15;Application Name=ColombusProbe"
$cn = New-Object System.Data.SqlClient.SqlConnection $cs
$cn.Open()
try {
    $cmd = $cn.CreateCommand()
    $cmd.CommandText = $Query
    $cmd.CommandTimeout = $Timeout
    $da = New-Object System.Data.SqlClient.SqlDataAdapter $cmd
    $ds = New-Object System.Data.DataSet
    [void]$da.Fill($ds)

    foreach ($dt in $ds.Tables) {
        $rows = $dt | Select-Object -Property $dt.Columns.ColumnName
        switch ($As) {
            'json'  { if ($null -eq $rows) { '[]' } else { , $rows | ConvertTo-Json -Depth 5 -Compress } }
            'csv'   { $rows | ConvertTo-Csv -NoTypeInformation }
            'table' { $rows | Format-Table -AutoSize | Out-String -Width 400 }
        }
    }
}
finally { $cn.Close() }
