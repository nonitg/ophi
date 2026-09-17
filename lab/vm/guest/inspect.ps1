# Step 0 of the ingestion plan: non-SQL recon. Highest yield per hour, and it runs before
# a single query is issued. Writes JSON to C:\colombus\out\ for the host to pull.
$ErrorActionPreference = 'Continue'
$out = 'C:\colombus\out'
New-Item -ItemType Directory -Force -Path $out | Out-Null

function Save($name, $obj) {
    $p = Join-Path $out "$name.json"
    $obj | ConvertTo-Json -Depth 6 | Set-Content -Path $p -Encoding utf8
    Write-Host ("{0,-24} -> {1}" -f $name, $p)
}

# --- machine ---------------------------------------------------------------
Save 'machine' ([ordered]@{
    hostname = $env:COMPUTERNAME
    user     = $env:USERNAME
    os       = (Get-CimInstance Win32_OperatingSystem).Caption
    build    = (Get-CimInstance Win32_OperatingSystem).BuildNumber
    arch     = $env:PROCESSOR_ARCHITECTURE
    dotnet   = (Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full' -ErrorAction SilentlyContinue | Get-ItemProperty).Version
    ips      = @((Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' }).IPAddress)
})

# --- installed products ----------------------------------------------------
$keys = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
Save 'installed' (Get-ItemProperty $keys -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName } |
    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
    Sort-Object DisplayName)

# --- SQL Server ------------------------------------------------------------
$instances = @()
$rk = 'HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL'
if (Test-Path $rk) {
    (Get-Item $rk).GetValueNames() | ForEach-Object { $instances += [ordered]@{ name = $_; id = (Get-ItemProperty $rk).$_ } }
}
Save 'sql' ([ordered]@{
    instances = $instances
    services  = @(Get-Service | Where-Object { $_.Name -match 'MSSQL|SQLAgent|SQLBrowser' } |
                    Select-Object Name, DisplayName, Status, StartType)
    listening = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
                    Where-Object { $_.LocalPort -in 1433, 1434 } | Select-Object LocalAddress, LocalPort)
})

# --- ABELDent on disk ------------------------------------------------------
$root = 'C:\ABELDent'
if (Test-Path $root) {
    # The plan flags .rpt / .rdl / .sql / .config as vendor-authored schema evidence.
    Save 'abeldent_files' (Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -match '^\.(sql|rpt|rdl|xsd|edmx|dbml|config|ini|chm|xml)$' } |
        Select-Object FullName, Length, LastWriteTime | Sort-Object FullName)

    Save 'abeldent_tree' (Get-ChildItem $root -Directory -Recurse -Depth 3 -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName)

    # Connection strings tell us the instance name and database name for free.
    $conn = @()
    Get-ChildItem $root -Recurse -Include *.config, *.ini -ErrorAction SilentlyContinue | ForEach-Object {
        $t = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($t -match 'Data Source|Initial Catalog|Server=|Database=') {
            $conn += [ordered]@{ file = $_.FullName; text = $t }
        }
    }
    Save 'abeldent_connstrings' $conn

    Save 'abeldent_exes' (Get-ChildItem $root -Recurse -Include *.exe, *.dll -ErrorAction SilentlyContinue |
        Select-Object Name, FullName, Length, @{n = 'Version'; e = { $_.VersionInfo.FileVersion } } |
        Sort-Object Name)

    Save 'abeldent_backups' (Get-ChildItem "$root\Data" -Recurse -Include *.bak -ErrorAction SilentlyContinue |
        Select-Object FullName, Length, LastWriteTime)
}
else { Write-Host 'C:\ABELDent not found — is ABELDent installed?' -ForegroundColor Yellow }

# --- EULA (week-1 action #3 in PLAN.md) ------------------------------------
Save 'eula_candidates' (Get-ChildItem 'C:\' -Recurse -Depth 4 -Include *eula*, *license*, *licence*, *terms* `
        -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'ABEL' } |
    Select-Object FullName, Length)

Write-Host "`ndone — pull with:  ./lab/vm/vm pull" -ForegroundColor Green
