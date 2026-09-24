# Fixed entry point for the OphiRun scheduled task.
# The guest agent runs as SYSTEM, but ABELDent's database is a LocalDB instance owned by
# the logged-on user — SYSTEM resolving (LOCALDB)\MSSQLLOCALDB would get its own empty
# instance instead. This bounces a command into the interactive session, which is also
# the only session that can see the desktop for screenshots.
$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory -Force -Path 'C:\ophi\out' | Out-Null
$out = 'C:\ophi\out\_ulast.txt'

$text = try { (& 'C:\ophi\_ucmd.ps1' *>&1 | Out-String) } catch { $_ | Out-String }

# BOM-free UTF-8: the host parses this as JSON, and PowerShell 5.1's -Encoding utf8
# emits a BOM that breaks every JSON reader on the other side.
[IO.File]::WriteAllText($out, $text + "`n___OPHI_UDONE___`n", (New-Object Text.UTF8Encoding $false))
