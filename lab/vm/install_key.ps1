# Run once in the VM as admin: authorises the host's SSH key for lab/vm/vm's ssh transport.
# Default path is the dockur/windows host share; pass -PubKey for anything else.
# Host side, ~/.ssh/config:  Host abelvm / HostName <vm ip> / User <windows user> / IdentityFile ~/.ssh/abeldent_vm
param([string]$PubKey = '\\host.lan\Data\.ssh\abeldent_vm.pub')
$f = 'C:\ProgramData\ssh\administrators_authorized_keys'
Get-Content $PubKey | Add-Content $f
# sshd ignores this file for admins unless only Administrators/SYSTEM can access it
icacls $f /inheritance:r /grant Administrators:F /grant SYSTEM:F
