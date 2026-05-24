# Publish Logistics project to GitHub (run after: gh auth login)
param(
    [string]$RepoName = "logistics-analytics-tracking",
    [ValidateSet("public", "private")]
    [string]$Visibility = "public"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

if (-not (git rev-parse --git-dir 2>$null)) {
    git init
    git branch -M main
}

if (-not (git rev-parse HEAD 2>$null)) {
    Write-Host "No commits. Stage and commit first." -ForegroundColor Red
    exit 1
}

$remote = git remote get-url origin 2>$null
if (-not $remote) {
    gh repo create $RepoName --$Visibility --source=. --remote=origin --description "Enterprise logistics analytics: shipment tracking, ML ETA/delay models, and Power BI-style KPIs"
}

git push -u origin main
Write-Host "Done. View repo:" -ForegroundColor Green
gh repo view --web
