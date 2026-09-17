# UI Automation driver for ABELDent (WPF). Runs in the logged-on user's session via `vm uexec`.
# Every verb prints what it did or a clear failure line; the host judges on content.
#
#   ui.ps1 tree  [-Name X | -Id X] [-Depth 3]      dump the control tree under a control (or the main window)
#   ui.ps1 click -Id X | -Name X                   Invoke / Toggle / Select, else click centre
#   ui.ps1 type  -Text '...' [-Id X | -Name X]     focus a control, select all, type
#   ui.ps1 keys  -Text '{ENTER}'                   raw SendKeys to the foreground window
#   ui.ps1 read  -Id X | -Name X                   Value / Text / Name of a control
#   ui.ps1 windows                                 top-level windows (dialogs show up here)
#   ui.ps1 wait  -Name X [-Timeout 10]             wait for a control to appear
param(
    [Parameter(Position = 0)][string]$Verb = 'tree',
    [string]$Name, [string]$Id, [string]$Text, [string]$Type,
    [string]$Window = 'ABELDent',
    [int]$Depth = 3, [int]$Timeout = 10, [switch]$Partial
)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms
$A = [System.Windows.Automation.AutomationElement]
$root = $A::RootElement
$true_ = [System.Windows.Automation.Condition]::TrueCondition

function Win {
    # Prefer the exact title; fall back to any top-level window whose title starts with $Window.
    foreach ($w in $root.FindAll('Children', $true_)) {
        if ($w.Current.Name -like "$Window*") { return $w }
    }
    $null
}

function Find($scope) {
    if (-not $scope) { $scope = Win }
    if (-not $scope) { return $null }
    $deadline = (Get-Date).AddSeconds($Timeout)
    do {
        if ($Id) {
            $c = New-Object System.Windows.Automation.PropertyCondition($A::AutomationIdProperty, $Id)
            $e = $scope.FindFirst('Descendants', $c)
            if ($e) { return $e }
        }
        if ($Name) {
            if ($Partial) {
                foreach ($e in $scope.FindAll('Descendants', $true_)) {
                    if ($e.Current.Name -like "*$Name*") { return $e }
                }
            } else {
                $c = New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, $Name)
                $e = $scope.FindFirst('Descendants', $c)
                if ($e) { return $e }
            }
        }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    $null
}

function Describe($e) {
    $c = $e.Current
    $r = $c.BoundingRectangle
    "{0} | name='{1}' | id='{2}' | class={3} | {4},{5} {6}x{7}{8}" -f $c.ControlType.ProgrammaticName.Replace('ControlType.', ''),
        $c.Name, $c.AutomationId, $c.ClassName, [int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height,
        $(if ($c.IsOffscreen) { ' OFFSCREEN' } else { '' })
}

function Walk($e, $d) {
    if ($d -gt $Depth) { return }
    foreach ($k in $e.FindAll('Children', $true_)) {
        $c = $k.Current
        if ($c.Name -or $c.AutomationId -or $d -le 1) { ('  ' * $d) + (Describe $k) }
        Walk $k ($d + 1)
    }
}

function ClickCentre($e) {
    $r = $e.Current.BoundingRectangle
    if ($r.Width -le 0) { throw 'control has no on-screen rectangle' }
    $x = [int]($r.X + $r.Width / 2); $y = [int]($r.Y + $r.Height / 2)
    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, $y)
    Start-Sleep -Milliseconds 80
    $sig = '[DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, System.UIntPtr i);'
    $m = Add-Type -MemberDefinition $sig -Name M -Namespace W32 -PassThru
    $m::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60; $m::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    "clicked centre ($x,$y)"
}

switch ($Verb) {
    'windows' {
        foreach ($w in $root.FindAll('Children', $true_)) {
            if ($w.Current.Name) { Describe $w }
        }
    }
    'tree' {
        $scope = if ($Id -or $Name) { Find } else { Win }
        if (-not $scope) { "not found: id='$Id' name='$Name'"; exit 1 }
        Describe $scope
        Walk $scope 1
    }
    'wait' {
        $e = Find
        if ($e) { 'found: ' + (Describe $e) } else { "timeout: id='$Id' name='$Name'"; exit 1 }
    }
    'read' {
        $e = Find
        if (-not $e) { "not found: id='$Id' name='$Name'"; exit 1 }
        $v = $null
        if ($e.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$v)) { 'value: ' + $v.Current.Value }
        elseif ($e.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern, [ref]$v)) { 'text: ' + $v.DocumentRange.GetText(4000) }
        else { 'name: ' + $e.Current.Name }
    }
    'click' {
        $e = Find
        if (-not $e) { "not found: id='$Id' name='$Name'"; exit 1 }
        $p = $null
        if ($e.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$p)) { $p.Invoke(); 'invoked: ' + (Describe $e) }
        elseif ($e.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$p)) { $p.Select(); 'selected: ' + (Describe $e) }
        elseif ($e.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern, [ref]$p)) { $p.Toggle(); 'toggled: ' + (Describe $e) }
        elseif ($e.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$p)) { $p.Expand(); 'expanded: ' + (Describe $e) }
        else { (ClickCentre $e) + ' on ' + (Describe $e) }
    }
    'type' {
        if ($Id -or $Name) {
            $e = Find
            if (-not $e) { "not found: id='$Id' name='$Name'"; exit 1 }
            $p = $null
            if ($e.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$p) -and -not $p.Current.IsReadOnly) {
                $p.SetValue($Text); 'set value on ' + (Describe $e); break
            }
            try { $e.SetFocus() } catch { ClickCentre $e | Out-Null }
            Start-Sleep -Milliseconds 150
        }
        [System.Windows.Forms.SendKeys]::SendWait('^a')
        [System.Windows.Forms.SendKeys]::SendWait($Text)
        "typed '$Text'"
    }
    'keys' {
        [System.Windows.Forms.SendKeys]::SendWait($Text)
        "sent '$Text'"
    }
    default { "unknown verb $Verb"; exit 1 }
}
