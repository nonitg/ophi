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
    [string]$Name, [string]$Id, [string]$Text, [string]$Type, [int]$X = -1, [int]$Y = -1,
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
    # Offscreen controls report an infinite/empty rect; Int32 cast throws on it.
    $geo = if ([double]::IsInfinity($r.X) -or $r.IsEmpty) { 'no-rect' } else { '{0},{1} {2}x{3}' -f [int]$r.X, [int]$r.Y, [int]$r.Width, [int]$r.Height }
    "{0} | name='{1}' | id='{2}' | class={3} | {4}{5}" -f $c.ControlType.ProgrammaticName.Replace('ControlType.', ''),
        $c.Name, $c.AutomationId, $c.ClassName, $geo, $(if ($c.IsOffscreen) { ' OFFSCREEN' } else { '' })
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
    ClickXY ([int]($r.X + $r.Width / 2)) ([int]($r.Y + $r.Height / 2))
}

# Screen-coordinate click. Needed because ABELDent's patient-file views (Treatment, Perio,
# Imaging) are not exposed through UI Automation at all; the screenshot is the only map.
function RClickXY($x, $y) {
    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, $y)
    Start-Sleep -Milliseconds 80
    $sig = '[DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, System.UIntPtr i);'
    $m = Add-Type -MemberDefinition $sig -Name M2 -Namespace W32 -PassThru
    $m::mouse_event(8, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60; $m::mouse_event(16, 0, 0, 0, [UIntPtr]::Zero)
    "right-clicked ($x,$y)"
}

function ClickXY($x, $y, $double = $false) {
    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, $y)
    Start-Sleep -Milliseconds 80
    $sig = '[DllImport("user32.dll")] public static extern void mouse_event(uint f, uint x, uint y, uint d, System.UIntPtr i);'
    $m = Add-Type -MemberDefinition $sig -Name M -Namespace W32 -PassThru
    $m::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60; $m::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
    if ($double) { Start-Sleep -Milliseconds 80; $m::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 60; $m::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero) }
    "clicked ($x,$y)"
}

function FocusedElement {
    $f = $A::FocusedElement
    if ($f) { 'focus: ' + (Describe $f) } else { 'focus: none' }
}

# WinForms AutomationIds are HWNDs and change every time a dialog opens, so fields are located
# by their label: the EDIT control on the same row, to the right of the STATIC named $Name.
function FieldByLabel {
    $scope = Win
    if (-not $scope) { return $null }
    # Several controls can share the label text (dashboard TextBlocks, headers); take the first
    # on-screen label that actually has an edit box on its row.
    $edits = @()
    foreach ($e in $scope.FindAll('Descendants', $true_)) {
        if ($e.Current.ClassName -match 'EDIT|TextBox' -and -not [double]::IsInfinity($e.Current.BoundingRectangle.X)) { $edits += $e }
    }
    $labels = $scope.FindAll('Descendants', (New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, $Name)))
    foreach ($label in $labels) {
        $lr = $label.Current.BoundingRectangle
        if ([double]::IsInfinity($lr.X) -or $label.Current.IsOffscreen) { continue }
        $best = $null
        foreach ($e in $edits) {
            $r = $e.Current.BoundingRectangle
            if ([Math]::Abs(($r.Y + $r.Height / 2) - ($lr.Y + $lr.Height / 2)) -lt 8 -and $r.X -gt $lr.X) {
                if (-not $best -or $r.X -lt $best.Current.BoundingRectangle.X) { $best = $e }
            }
        }
        if ($best) { return $best }
    }
    $null
}

function SetField($e, $text) {
    $p = $null
    if ($e.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$p) -and -not $p.Current.IsReadOnly) {
        $p.SetValue($text); Start-Sleep -Milliseconds 150
        if ($p.Current.Value -eq $text) { return 'set: ' + (Describe $e) }
    }
    try { $e.SetFocus() } catch { ClickCentre $e | Out-Null }
    Start-Sleep -Milliseconds 150
    # Legacy WinForms TextBoxes do not bind Ctrl+A; select Home..End instead.
    [System.Windows.Forms.SendKeys]::SendWait('{HOME}+{END}{BACKSPACE}')
    if ($text) { [System.Windows.Forms.SendKeys]::SendWait($text) }
    Start-Sleep -Milliseconds 150
    $now = if ($p) { $p.Current.Value } else { '?' }
    'typed; value now [' + $now + '] on ' + (Describe $e)
}

# Guard: never send blind clicks or keystrokes while a claims/submission window is in front.
# A stray keystroke once opened Print/Submit Claims -> Select Transactions to Submit; a blind click
# there could transmit a claim. Named clicks on 'Cancel' remain allowed.
function ForegroundIsSubmission {
    $f = $A::FocusedElement
    while ($f -and $f.Current.ControlType -ne [System.Windows.Automation.ControlType]::Window) {
        $f = [System.Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($f)
    }
    $titles = @()
    if ($f) { $titles += $f.Current.Name }
    foreach ($w in $root.FindAll('Children', $true_)) { if (-not $w.Current.IsOffscreen) { $titles += $w.Current.Name } }
    foreach ($t in $titles) { if ($t -match 'Submit|CDAnet|Print Forms|EDI|Claim') { return $t } }
    $null
}

if ($Verb -in 'clickxy', 'dblclick', 'keys', 'type') {
    $blocked = ForegroundIsSubmission
    if ($blocked) { "REFUSED: '$blocked' is open; cancel it by name first (scripts/vm-dismiss-submit-dialogs.sh)"; exit 1 }
}

switch ($Verb) {
    'setfield' {
        $e = FieldByLabel
        if (-not $e) { "no edit found beside label '$Name'"; exit 1 }
        SetField $e $Text
    }
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
            SetField $e $Text
        } else {
            [System.Windows.Forms.SendKeys]::SendWait('^a')
            [System.Windows.Forms.SendKeys]::SendWait($Text)
            "typed '$Text' into the focused control"
        }
    }
    'clickxy'  { ClickXY $X $Y }
    'rclick'   { RClickXY $X $Y }
    'dblclick' { ClickXY $X $Y $true }
    'focus'    { FocusedElement }
    'keys' {
        [System.Windows.Forms.SendKeys]::SendWait($Text)
        "sent '$Text'"
    }
    default { "unknown verb $Verb"; exit 1 }
}
