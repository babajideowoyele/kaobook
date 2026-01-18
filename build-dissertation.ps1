# Build dissertation
# Run from kaobook root: .\build-dissertation.ps1

Set-Location $PSScriptRoot
latexmk -pdf -outdir=dissertation dissertation/main.tex

Write-Host "`nPDF at: dissertation/main.pdf" -ForegroundColor Green
