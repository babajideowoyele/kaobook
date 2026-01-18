# build.ps1 - Build kaobook dissertation
# Usage: .\build.ps1 [clean]
# Output: dissertation/main.pdf

param([string]$Mode = "build")

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DissDir = Join-Path $RepoRoot "dissertation"

Set-Location $RepoRoot

switch ($Mode.ToLower()) {
    "clean" {
        Write-Host "Cleaning auxiliary files..." -ForegroundColor Yellow
        $auxExts = @("*.aux", "*.bbl", "*.bcf", "*.blg", "*.fdb_latexmk", "*.fls",
                     "*.idx", "*.ilg", "*.ind", "*.lof", "*.log", "*.lot", "*.out",
                     "*.run.xml", "*.toc", "*.synctex.gz", "*.mw")
        foreach ($ext in $auxExts) {
            Remove-Item -Path (Join-Path $DissDir $ext) -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Done" -ForegroundColor Green
    }
    default {
        Write-Host "Building dissertation..." -ForegroundColor Cyan

        # Run lualatex + biber + lualatex x2 (kaobook requires LuaLaTeX or XeLaTeX)
        Push-Location $RepoRoot

        Write-Host "  Pass 1: lualatex..." -ForegroundColor Gray
        lualatex -shell-escape -interaction=nonstopmode -output-directory=dissertation dissertation/main.tex | Out-Null

        Write-Host "  Pass 2: biber..." -ForegroundColor Gray
        biber dissertation/main 2>$null

        Write-Host "  Pass 3: lualatex..." -ForegroundColor Gray
        lualatex -shell-escape -interaction=nonstopmode -output-directory=dissertation dissertation/main.tex | Out-Null

        Write-Host "  Pass 4: lualatex..." -ForegroundColor Gray
        lualatex -shell-escape -interaction=nonstopmode -output-directory=dissertation dissertation/main.tex | Out-Null

        Pop-Location

        $PdfPath = Join-Path $DissDir "main.pdf"
        if (Test-Path $PdfPath) {
            $Size = [math]::Round((Get-Item $PdfPath).Length / 1MB, 1)
            Write-Host "`nDone: dissertation/main.pdf ($Size MB)" -ForegroundColor Green
        } else {
            Write-Host "`nFailed - check dissertation/main.log" -ForegroundColor Red
        }
    }
}
