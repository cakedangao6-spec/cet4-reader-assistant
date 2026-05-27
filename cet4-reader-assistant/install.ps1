$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$supportedPythonPattern = "^3\.(9|10|11|12|13)\."

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

function Get-PythonVersion {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    $version = & $Command @Arguments -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    return ($version | Select-Object -First 1).Trim()
}

function Test-SupportedPython {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    $version = Get-PythonVersion $Command $Arguments
    return $null -ne $version -and $version -match $supportedPythonPattern
}

function Test-CanCreateVenv {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    $probeDir = Join-Path $PSScriptRoot ".venv_probe"
    if (Test-Path $probeDir) {
        Remove-Item -LiteralPath $probeDir -Recurse -Force
    }

    try {
        & $Command @Arguments -m venv --without-pip $probeDir 2>$null
        $ok = $LASTEXITCODE -eq 0 -and (Test-Path (Join-Path $probeDir "Scripts\python.exe"))
    }
    catch {
        $ok = $false
    }

    if (Test-Path $probeDir) {
        Remove-Item -LiteralPath $probeDir -Recurse -Force
    }
    return $ok
}

function Get-PythonCommand {
    $candidates = New-Object System.Collections.Generic.List[object]

    if ($env:CET4_PYTHON) {
        $candidates.Add(@{
            Command = $env:CET4_PYTHON
            Args = @()
        })
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($minor in 13, 12, 11, 10, 9) {
            $candidates.Add(@{
                Command = "py"
                Args = @("-3.$minor")
            })
        }
    }

    $wherePython = & where.exe python 2>$null
    foreach ($pythonPath in $wherePython) {
        if ($pythonPath) {
            $candidates.Add(@{
                Command = $pythonPath.Trim()
                Args = @()
            })
        }
    }

    $codexRuntimePython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $codexRuntimePython) {
        $candidates.Add(@{
            Command = $codexRuntimePython
            Args = @()
        })
    }

    foreach ($candidate in $candidates) {
        if (
            (Test-SupportedPython $candidate.Command $candidate.Args) -and
            (Test-CanCreateVenv $candidate.Command $candidate.Args)
        ) {
            return $candidate
        }
    }

    throw "No usable Python found. Please install Python 3.9-3.13, then run again."
}

function Reset-VenvIfUnsupported {
    if (-not (Test-Path $venvPython)) {
        return
    }

    if (Test-SupportedPython $venvPython @()) {
        return
    }

    $venvRoot = Resolve-Path (Join-Path $PSScriptRoot ".venv")
    $projectRoot = Resolve-Path $PSScriptRoot
    if (-not $venvRoot.Path.StartsWith($projectRoot.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove unexpected virtual environment path: $($venvRoot.Path)"
    }

    Write-Host "Existing .venv uses an unsupported Python version. Recreating it..."
    Remove-Item -LiteralPath $venvRoot.Path -Recurse -Force
}

Reset-VenvIfUnsupported
$pythonCommand = Get-PythonCommand

if (-not (Test-Path $venvPython)) {
    Invoke-Checked $pythonCommand.Command (@($pythonCommand.Args) + @("-m", "venv", ".venv"))
}

Invoke-Checked $venvPython @("-m", "pip", "install", "--upgrade", "pip")
try {
    Invoke-Checked $venvPython @("-m", "pip", "install", "paddlepaddle==3.3.1", "-i", "https://www.paddlepaddle.org.cn/packages/stable/cpu/")
}
catch {
    Write-Warning "Official PaddlePaddle mirror failed. Falling back to PyPI."
    Invoke-Checked $venvPython @("-m", "pip", "install", "paddlepaddle==3.3.1")
}
Invoke-Checked $venvPython @("-m", "pip", "install", "-r", ".\requirements.txt")

try {
    Invoke-Checked $venvPython @(".\scripts\download_dictionary.py")
}
catch {
    Write-Warning "Dictionary download failed. The app will keep using bundled offline data when available."
}

Invoke-Checked $venvPython @("-m", "unittest", "discover", "-s", "tests", "-v")
