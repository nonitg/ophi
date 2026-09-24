# Capture the interactive desktop. Must run in the logged-on user's session, not the SSH
# session — an SSH-spawned process captures a black screen. Driven via a scheduled task.
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
New-Item -ItemType Directory -Force -Path 'C:\ophi\out' | Out-Null
$bmp.Save('C:\ophi\out\shot.png', [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
