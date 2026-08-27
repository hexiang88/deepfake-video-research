# Convert research Markdown to Word with working hyperlinks and Chinese-friendly styles.
# Example:
#   powershell -File scripts/md-to-docx.ps1
#   powershell -File scripts/md-to-docx.ps1 -InputFile research/reports/audio.md

param(
    [string]$InputFile = "",
    [string]$OutDir = "export/docx"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$lua = Join-Path $PSScriptRoot "md-to-docx.lua"
$ref = Join-Path $PSScriptRoot "docx-reference.docx"
$outRoot = Join-Path $repo $OutDir
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null

if (-not (Test-Path $ref)) {
    $tmp = Join-Path $env:TEMP "empty-md-to-docx.md"
    Set-Content -Path $tmp -Value "# Heading`n`nParagraph.`n" -Encoding utf8
    & pandoc $tmp -o $ref --quiet
}

$files = @()
if ($InputFile) {
    $files = @(Resolve-Path $InputFile)
} else {
    $files = @(
        "research/datasets/audio.md",
        "research/datasets/video.md",
        "research/reports/audio.md",
        "research/reports/video.md",
        "research/coverage-matrix.md",
        "research/benchmark-mapping.md",
        "research/developer-selection-matrix.md"
    ) | ForEach-Object { Join-Path $repo $_ } | Where-Object { Test-Path $_ }
}

$env:DOCX_SRC_ROOT = $repo
$env:DOCX_OUT_ROOT = $outRoot

foreach ($src in $files) {
    $src = [string]$src
    $rel = $src.Substring($repo.Length).TrimStart("\", "/")
    $dest = Join-Path $outRoot ($rel -replace "\.md$", ".docx")
    $destDir = Split-Path $dest -Parent
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    $env:DOCX_THIS_OUT = $dest

    & pandoc $src `
        -f markdown+pipe_tables+autolink_bare_uris+gfm_auto_identifiers `
        -t docx `
        --lua-filter=$lua `
        --reference-doc=$ref `
        --toc `
        --toc-depth=2 `
        --wrap=none `
        --resource-path="$(Split-Path $src -Parent)" `
        -o $dest

    if ($LASTEXITCODE -ne 0) {
        throw "pandoc failed for $src"
    }
    Write-Host "Wrote $dest"
}

Write-Host ""
Write-Host "Open the folder: $outRoot"
Write-Host "GitHub/arXiv links stay as https. Cross-file .md links point at the matching .docx in this folder."
Write-Host "To improve fonts/tables: open scripts/docx-reference.docx in Word, set 微软雅黑 + Table Grid, save, then rerun this script."
