param([Parameter(Mandatory = $true)][string]$GodotPath)
$ErrorActionPreference = 'Stop'
$projectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$executable = (Resolve-Path -LiteralPath $GodotPath).Path
$logDir = Join-Path (Split-Path $projectDir -Parent) 'logs/godot'
New-Item -ItemType Directory -Force $logDir | Out-Null
$testLog = Join-Path $logDir 'tests.log'
$process = Start-Process -FilePath $executable -ArgumentList @('--headless', '--path', ('"' + $projectDir + '"'), '--script', 'res://tests/run_tests.gd', '--log-file', ('"' + $testLog + '"')) -WindowStyle Hidden -PassThru -Wait
Get-Content -LiteralPath $testLog
if ($process.ExitCode -ne 0 -or (Select-String -LiteralPath $testLog -Pattern 'SCRIPT ERROR|ERROR:|FAIL:') -or -not (Select-String -LiteralPath $testLog -Pattern 'GODOT TESTS: .* 0 failures')) {
    throw 'Godot validation failed. See tests.log.'
}
$visualLog = Join-Path $logDir 'visual-tests.log'
$visualProcess = Start-Process -FilePath $executable -ArgumentList @('--headless', '--path', ('"' + $projectDir + '"'), '--script', 'res://tests/visual_regression.gd', '--log-file', ('"' + $visualLog + '"')) -WindowStyle Hidden -PassThru -Wait
Get-Content -LiteralPath $visualLog
if ($visualProcess.ExitCode -ne 0 -or (Select-String -LiteralPath $visualLog -Pattern 'SCRIPT ERROR|ERROR:|FAIL:') -or -not (Select-String -LiteralPath $visualLog -Pattern 'VISUAL TESTS: .* 0 failures')) {
    throw 'Godot visual regression failed. See visual-tests.log.'
}
$gddLog = Join-Path $logDir 'gdd-tests.log'
$gddProcess = Start-Process -FilePath $executable -ArgumentList @('--headless', '--path', ('"' + $projectDir + '"'), '--script', 'res://tests/gdd_features.gd', '--log-file', ('"' + $gddLog + '"')) -WindowStyle Hidden -PassThru -Wait
Get-Content -LiteralPath $gddLog
if ($gddProcess.ExitCode -ne 0 -or (Select-String -LiteralPath $gddLog -Pattern 'SCRIPT ERROR|ERROR:|FAIL:') -or -not (Select-String -LiteralPath $gddLog -Pattern 'GDD TESTS: .* 0 failures')) {
    throw 'Godot GDD feature validation failed. See gdd-tests.log.'
}
