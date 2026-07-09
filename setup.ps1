# setup.ps1 — richtet das Dashboard-Monorepo auf diesem Rechner ein.
# Idempotent: bestehende venvs werden uebersprungen. Details im README.md.
#
#   Aufruf:  powershell -ExecutionPolicy Bypass -File setup.ps1
#
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- 1. Python finden (3.11+) --------------------------------------------
$python = $null
foreach ($cand in @("py -3.13", "py -3.12", "py -3.11", "python")) {
    $exe = $cand.Split(" ")[0]
    if (Get-Command $exe -ErrorAction SilentlyContinue) {
        try {
            $v = & $exe $cand.Split(" ")[1..99] --version 2>$null
            if ($v -match "Python 3\.(1[1-9])") { $python = $cand; break }
        } catch {}
    }
}
if (-not $python) {
    Write-Host "FEHLER: Kein Python 3.11+ gefunden. Bitte von python.org installieren." -ForegroundColor Red
    exit 1
}
Write-Host "Python: $python ($(& $python.Split(' ')[0] $python.Split(' ')[1..99] --version))" -ForegroundColor Green

# --- 2. venvs erstellen + Abhaengigkeiten installieren ---------------------
# basel-ai-landing braucht kein venv (reine stdlib).
foreach ($proj in @("ai-command-center", "trading-agent", "basel-ai-buchung")) {
    $dir = Join-Path $root $proj
    $venv = Join-Path $dir ".venv"
    if (Test-Path (Join-Path $venv "Scripts\python.exe")) {
        Write-Host "[$proj] venv vorhanden - uebersprungen" -ForegroundColor DarkGray
    } else {
        Write-Host "[$proj] erstelle venv + installiere requirements..." -ForegroundColor Cyan
        $parts = $python.Split(" ")
        & $parts[0] ($parts[1..99] + @("-m", "venv", $venv))
        & (Join-Path $venv "Scripts\python.exe") -m pip install --upgrade pip --quiet
        & (Join-Path $venv "Scripts\python.exe") -m pip install -r (Join-Path $dir "requirements.txt")
        if (-not $?) { Write-Host "[$proj] pip install fehlgeschlagen!" -ForegroundColor Red; exit 1 }
        Write-Host "[$proj] fertig" -ForegroundColor Green
    }
}

# --- 3. Externe Repos pruefen (nur Warnung) --------------------------------
$reposRoot = Split-Path -Parent $root
foreach ($r in @("SecondBrain-Leo", "2526_KI1_GdP_C", "2526_KI1_DatB")) {
    if (-not (Test-Path (Join-Path $reposRoot $r))) {
        Write-Host "WARNUNG: Geschwister-Repo fehlt: $reposRoot\$r" -ForegroundColor Yellow
        Write-Host "         -> git clone https://github.com/sternlb/$r `"$reposRoot\$r`"" -ForegroundColor Yellow
    }
}

# --- 4. gh CLI pruefen (Repo-Kacheln im Command Center, nur Warnung) -------
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh auth status *> $null
    if (-not $?) { Write-Host "WARNUNG: gh CLI nicht eingeloggt (gh auth login) - Repo-Kacheln bleiben leer." -ForegroundColor Yellow }
} else {
    Write-Host "WARNUNG: gh CLI fehlt (winget install GitHub.cli) - Repo-Kacheln bleiben leer." -ForegroundColor Yellow
}

# --- 5. Secrets pruefen (nur Hinweis, Beschaffung siehe README) ------------
$secrets = @(
    "ai-command-center\credentials.json",
    "ai-command-center\token.json",
    "basel-ai-buchung\credentials.json",
    "basel-ai-buchung\token.json",
    "trading-agent\data\holdings.csv"
)
$missing = $secrets | Where-Object { -not (Test-Path (Join-Path $root $_)) }
if ($missing) {
    Write-Host ""
    Write-Host "Fehlende lokale Dateien (gitignored, siehe README 'Secrets'):" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host "Die Server starten trotzdem; betroffene Sektionen bleiben leer." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup fertig. Starten mit: start_dashboards.bat" -ForegroundColor Green
