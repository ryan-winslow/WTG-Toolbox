i need a powershell script that will run on windows. It should check to see if python is installed, then install it if not. After that it will check again, then run the wtg_toolbox.py script in github
wtg_toolbox.py

I’ll build this as a Windows PowerShell launcher. One important detail: the repository is private, so the normal GitHub page URL cannot be downloaded anonymously; the launcher will need a GitHub token (or the repo/package must be made public). I’ll also account for the tools folder by downloading the whole repository, not only the .py file.
Read library skill

I’m using the file-creation workflow so you’ll get a reusable .ps1 download. The script will prompt securely for a GitHub token if GITHUB_TOKEN is not already set, install Python through Windows Package Manager when needed, verify Python again, download the private repository, and launch the toolbox.
Executed WTGToolbox script

The launcher is complete. I’m saving the finished PowerShell file now; I’ve kept the token out of the file and out of command-line arguments.
Created library file for script execution


Library
/Launch-WTGToolbox.ps1

#Requires -Version 5.1

[CmdletBinding()]
param(
    [string]$GitHubOwner = "ryan-winslow",
    [string]$GitHubRepository = "WTG-Toolbox",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Get-PythonCommand {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        try {
            & py.exe -3 --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return @{ FilePath = "py.exe"; Arguments = @("-3") }
            }
        } catch { }
    }

    if (Get-Command python.exe -ErrorAction SilentlyContinue) {
        try {
            & python.exe --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return @{ FilePath = "python.exe"; Arguments = @() }
            }
        } catch { }
    }

    return $null
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

Write-Host "Checking for Python..." -ForegroundColor Cyan
$python = Get-PythonCommand

if (-not $python) {
    Write-Host "Python was not found. Installing Python 3.13..." -ForegroundColor Yellow

    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw "Windows Package Manager (winget) is not installed. Install 'App Installer' from Microsoft Store, then run this launcher again."
    }

    & winget.exe install --id Python.Python.3.13 -e --source winget `
        --accept-package-agreements --accept-source-agreements --silent

    if ($LASTEXITCODE -ne 0) {
        throw "Python installation failed. winget returned exit code $LASTEXITCODE."
    }

    Refresh-Path
    $python = Get-PythonCommand

    if (-not $python) {
        throw "Python installation completed, but Python still could not be found. Restart Windows and run this launcher again."
    }
}

$versionArgs = @($python.Arguments) + @("--version")
Write-Host -NoNewline "Python found: " -ForegroundColor Green
& $python.FilePath @versionArgs

$token = $env:GITHUB_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "A GitHub token with read access to the private repository is required." -ForegroundColor Yellow
    $secureToken = Read-Host "GitHub token" -AsSecureString
    $tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
    try {
        $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
    }
}

if ([string]::IsNullOrWhiteSpace($token)) {
    throw "No GitHub token was supplied."
}

$installRoot = Join-Path $env:LOCALAPPDATA "WTG-Toolbox"
$downloadRoot = Join-Path $env:TEMP ("WTG-Toolbox-" + [Guid]::NewGuid().ToString("N"))
$archivePath = Join-Path $downloadRoot "WTG-Toolbox.zip"
$extractPath = Join-Path $downloadRoot "Extracted"
$apiUrl = "https://api.github.com/repos/$GitHubOwner/$GitHubRepository/zipball/$Branch"

try {
    New-Item -ItemType Directory -Path $downloadRoot, $extractPath -Force | Out-Null

    Write-Host "Downloading the latest WTG Toolbox..." -ForegroundColor Cyan
    $headers = @{
        Authorization          = "Bearer $token"
        Accept                 = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
        "User-Agent"           = "WTG-Toolbox-PowerShell-Launcher"
    }

    Invoke-WebRequest -Uri $apiUrl -Headers $headers -OutFile $archivePath -UseBasicParsing
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractPath -Force

    $repoFolder = Get-ChildItem -LiteralPath $extractPath -Directory | Select-Object -First 1
    if (-not $repoFolder) {
        throw "The downloaded repository archive did not contain a repository folder."
    }

    if (Test-Path -LiteralPath $installRoot) {
        Remove-Item -LiteralPath $installRoot -Recurse -Force
    }
    Move-Item -LiteralPath $repoFolder.FullName -Destination $installRoot

    $toolboxScript = Join-Path $installRoot "wtg_toolbox.py"
    if (-not (Test-Path -LiteralPath $toolboxScript -PathType Leaf)) {
        throw "wtg_toolbox.py was not found in the downloaded repository."
    }

    Write-Host "Launching WTG Toolbox..." -ForegroundColor Green
    $launchArgs = @($python.Arguments) + @($toolboxScript)
    Push-Location $installRoot
    try {
        & $python.FilePath @launchArgs
        if ($LASTEXITCODE -ne 0) {
            throw "WTG Toolbox exited with code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    $token = $null
    $headers = $null
    if (Test-Path -LiteralPath $downloadRoot) {
        Remove-Item -LiteralPath $downloadRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

