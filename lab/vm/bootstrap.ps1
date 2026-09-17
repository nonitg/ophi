# Colombus lab bootstrap — run ONCE in an elevated PowerShell inside the Windows guest.
# Opens an SSH control channel from the Mac host so all further work is scripted, not clicked.
# Read-only intent: this installs no agent and touches no ABELDent data.

$ErrorActionPreference = 'Continue'
$pub = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBv0Z5+uNSlK9xAEvoKtNOq7FbsfmV20C49eSDRZenIh colombus-lab'

function Step($n) { Write-Host "`n=== $n ===" -ForegroundColor Cyan }

Step '1/6 OpenSSH Server'
$cap = Get-WindowsCapability -Online -Name OpenSSH.Server* | Select-Object -First 1
if ($cap.State -ne 'Installed') {
    Write-Host "installing $($cap.Name) ..."
    Add-WindowsCapability -Online -Name $cap.Name
} else { Write-Host 'already installed' }

Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
Set-Service -Name ssh-agent -StartupType Automatic -ErrorAction SilentlyContinue
Get-Service sshd | Format-Table Name, Status, StartType -AutoSize

Step '2/6 Firewall — SSH in from the host-only network'
if (-not (Get-NetFirewallRule -Name 'colombus-sshd' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name 'colombus-sshd' -DisplayName 'OpenSSH Server (Colombus lab)' `
        -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
}
Write-Host 'port 22 allowed inbound'

Step '3/6 Authorized key'
$admKeys = Join-Path $env:ProgramData 'ssh\administrators_authorized_keys'
Set-Content -Path $admKeys -Value $pub -Encoding ascii
icacls $admKeys /inheritance:r /grant 'Administrators:F' /grant 'SYSTEM:F' | Out-Null

$userSsh = Join-Path $env:USERPROFILE '.ssh'
New-Item -ItemType Directory -Force -Path $userSsh | Out-Null
Set-Content -Path (Join-Path $userSsh 'authorized_keys') -Value $pub -Encoding ascii
Write-Host "key installed for $env:USERNAME and for Administrators"

Step '4/6 Default SSH shell = PowerShell'
New-Item -Path 'HKLM:\SOFTWARE\OpenSSH' -Force | Out-Null
New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell `
    -Value 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -PropertyType String -Force | Out-Null
Restart-Service sshd
Write-Host 'sshd restarted'

Step '5/6 QEMU guest agent (second channel: utmctl exec / file transfer / clipboard)'
$iso = Get-Volume | Where-Object { $_.DriveType -eq 'CD-ROM' -and $_.FileSystemLabel -like '*UTM*' } | Select-Object -First 1
if ($iso) {
    $exe = Get-ChildItem "$($iso.DriveLetter):\" -Filter '*.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($exe) {
        Write-Host "running $($exe.FullName) /S (silent)"
        Start-Process -FilePath $exe.FullName -ArgumentList '/S' -Wait -ErrorAction SilentlyContinue
    } else { Write-Host 'no installer found on the UTM tools ISO — skip' }
} else { Write-Host 'UTM guest tools ISO not mounted — skip (optional)' }

Step '6/6 Inventory'
$o = [ordered]@{}
$o.hostname   = $env:COMPUTERNAME
$o.user       = $env:USERNAME
$o.os         = (Get-CimInstance Win32_OperatingSystem).Caption
$o.arch       = $env:PROCESSOR_ARCHITECTURE
$o.ips        = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' }).IPAddress -join ','
$o.abeldent   = (Test-Path 'C:\ABELDent')
$o.sqlservices = (Get-Service | Where-Object { $_.Name -like 'MSSQL*' } | ForEach-Object { "$($_.Name)=$($_.Status)" }) -join ' '
$o.GetEnumerator() | ForEach-Object { '{0,-12} {1}' -f $_.Key, $_.Value }

Write-Host "`nDONE. From the Mac:  ssh -i ~/.ssh/id_ed25519_abeldent $env:USERNAME@$(((Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like '192.168.64.*'}).IPAddress | Select-Object -First 1))" -ForegroundColor Green
