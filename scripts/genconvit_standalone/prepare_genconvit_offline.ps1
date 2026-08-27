param(
    [string]$OutDir = "$env:USERPROFILE\Downloads\genconvit-offline",
    [ValidateRange(1, 100)][int]$MaxDownloadAttempts = 20,
    [ValidateRange(1, 3600)][int]$RetryDelaySeconds = 15
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Use a stable .part filename with curl's HTTP Range support. Unlike the current
# hf CLI temporary-file lifecycle, this survives process exits and Ctrl+C.
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$OfficialRepo = "https://github.com/erprogs/GenConViT.git"
$OfficialCommit = "2c1d0bd7eecea94926595781a744e3f4b8b55290"
$HfRepo = "Deressa/GenConViT"
$HfRevision = "32d6e9e3c931a37971cc756da706cf1eef643372"
$EdFile = "genconvit_ed_inference.pth"
$VaeFile = "genconvit_vae_inference.pth"
$EdBytes = 238174949
$VaeBytes = 2782175601
$EdSha256 = "86f0c2e875016435def7d031b357bda5dc0061367290d73de121186df3f03f8c"
$VaeSha256 = "53c627c82d1439fc80e18ac462c1ed6969a3babe5376124a5c38d1c0c88c9042"

foreach ($CommandName in @("git", "curl.exe")) {
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Required command is missing: $CommandName"
    }
}

$ResolvedOutDir = [IO.Path]::GetFullPath($OutDir)
New-Item -ItemType Directory -Path $ResolvedOutDir -Force | Out-Null

$MirrorDir = Join-Path $ResolvedOutDir "GenConViT-mirror.git"
$BundleFile = Join-Path $ResolvedOutDir "GenConViT-$OfficialCommit.bundle"
$EdPath = Join-Path $ResolvedOutDir $EdFile
$VaePath = Join-Path $ResolvedOutDir $VaeFile

if (Test-Path -LiteralPath $MirrorDir) {
    $IsBare = git -C $MirrorDir rev-parse --is-bare-repository
    if ($LASTEXITCODE -ne 0 -or $IsBare.Trim() -ne "true") {
        throw "Existing mirror path is not a bare Git repository: $MirrorDir"
    }
    git -C $MirrorDir cat-file -e "$OfficialCommit^{commit}"
    if ($LASTEXITCODE -ne 0) {
        throw "Existing mirror does not contain pinned commit: $OfficialCommit"
    }
} else {
    git clone --mirror $OfficialRepo $MirrorDir
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub clone failed"
    }
}

$ResolvedCommit = (git -C $MirrorDir rev-parse "$OfficialCommit^{commit}").Trim()
if ($LASTEXITCODE -ne 0 -or $ResolvedCommit -ne $OfficialCommit) {
    throw "Pinned Git commit verification failed: $ResolvedCommit"
}
git -C $MirrorDir update-ref refs/heads/genconvit-eval-pinned $OfficialCommit
if ($LASTEXITCODE -ne 0) {
    throw "Could not create the pinned bundle ref"
}

if (Test-Path -LiteralPath $BundleFile) {
    $BundleHeads = git bundle list-heads $BundleFile
    if ($LASTEXITCODE -ne 0 -or $BundleHeads -notmatch [regex]::Escape($OfficialCommit)) {
        throw "Existing bundle does not advertise the pinned commit: $BundleFile"
    }
} else {
    git -C $MirrorDir bundle create $BundleFile refs/heads/genconvit-eval-pinned
    if ($LASTEXITCODE -ne 0) {
        throw "Git bundle creation failed"
    }
}
git -C $MirrorDir bundle verify $BundleFile
if ($LASTEXITCODE -ne 0) {
    throw "Git bundle integrity verification failed: $BundleFile"
}

function Assert-Sha256 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Expected
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
    $Actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected) {
        throw "SHA256 mismatch for $Path; expected $Expected, got $Actual"
    }
}

function Complete-PartialDownload {
    param(
        [Parameter(Mandatory = $true)][string]$PartialPath,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][long]$ExpectedBytes,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256
    )

    if (-not (Test-Path -LiteralPath $PartialPath -PathType Leaf)) {
        return $false
    }
    $PartialBytes = (Get-Item -LiteralPath $PartialPath).Length
    if ($PartialBytes -gt $ExpectedBytes) {
        throw (
            "Partial file is larger than expected; preserve it for inspection: " +
            "$PartialPath ($PartialBytes > $ExpectedBytes bytes)"
        )
    }
    if ($PartialBytes -ne $ExpectedBytes) {
        return $false
    }

    Assert-Sha256 -Path $PartialPath -Expected $ExpectedSha256
    if (Test-Path -LiteralPath $Destination) {
        throw "Refusing to replace an existing destination: $Destination"
    }
    Move-Item -LiteralPath $PartialPath -Destination $Destination
    Assert-Sha256 -Path $Destination -Expected $ExpectedSha256
    return $true
}

function Invoke-ResumableHfDownload {
    param(
        [Parameter(Mandatory = $true)][string]$Filename,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][long]$ExpectedBytes,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256
    )

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        Assert-Sha256 -Path $Destination -Expected $ExpectedSha256
        Write-Output "Already complete; skipping download: $Filename"
        return
    }

    $PartialPath = "$Destination.part"
    $DownloadUrl = "https://huggingface.co/$HfRepo/resolve/$HfRevision/${Filename}?download=true"
    if (Test-Path -LiteralPath $PartialPath -PathType Leaf) {
        $ExistingBytes = (Get-Item -LiteralPath $PartialPath).Length
        Write-Output (
            "Reusable partial file: {0} ({1:N2}/{2:N2} GiB)" -f
            $PartialPath, ($ExistingBytes / 1GB), ($ExpectedBytes / 1GB)
        )
        if (Complete-PartialDownload `
            -PartialPath $PartialPath `
            -Destination $Destination `
            -ExpectedBytes $ExpectedBytes `
            -ExpectedSha256 $ExpectedSha256
        ) {
            Write-Output "Completed partial file verified and finalized: $Filename"
            return
        }
    }

    for ($Attempt = 1; $Attempt -le $MaxDownloadAttempts; $Attempt++) {
        Write-Output (
            "Downloading {0}; attempt {1}/{2}. Existing .part data is retained." -f
            $Filename, $Attempt, $MaxDownloadAttempts
        )
        & curl.exe `
            --proto "=https" `
            --proto-redir "=https" `
            --location `
            --fail `
            --show-error `
            --continue-at - `
            --output $PartialPath `
            --connect-timeout 30 `
            --speed-limit 1024 `
            --speed-time 300 `
            --user-agent "genconvit-offline-prep/1.0" `
            $DownloadUrl
        $CurlExitCode = $LASTEXITCODE

        if (Test-Path -LiteralPath $PartialPath -PathType Leaf) {
            $CurrentBytes = (Get-Item -LiteralPath $PartialPath).Length
            Write-Output (
                "Saved partial progress: {0:N2}/{1:N2} GiB" -f
                ($CurrentBytes / 1GB), ($ExpectedBytes / 1GB)
            )
            if (Complete-PartialDownload `
                -PartialPath $PartialPath `
                -Destination $Destination `
                -ExpectedBytes $ExpectedBytes `
                -ExpectedSha256 $ExpectedSha256
            ) {
                Write-Output "Download verified and finalized: $Filename"
                return
            }
        }
        if ($CurlExitCode -eq 0) {
            Write-Warning "curl exited successfully before the expected byte count was reached."
        } else {
            Write-Warning "curl exited with code $CurlExitCode; saved bytes will be reused."
        }
        if ($Attempt -lt $MaxDownloadAttempts) {
            Write-Warning (
                "Download interrupted. Retrying in $RetryDelaySeconds seconds; " +
                "do not delete $PartialPath."
            )
            Start-Sleep -Seconds $RetryDelaySeconds
        }
    }

    throw (
        "Hugging Face download did not finish after $MaxDownloadAttempts attempts: " +
        "$Filename. Rerun the same command to continue from $PartialPath."
    )
}

Invoke-ResumableHfDownload `
    -Filename $EdFile `
    -Destination $EdPath `
    -ExpectedBytes $EdBytes `
    -ExpectedSha256 $EdSha256
Invoke-ResumableHfDownload `
    -Filename $VaeFile `
    -Destination $VaePath `
    -ExpectedBytes $VaeBytes `
    -ExpectedSha256 $VaeSha256

$BundleSha256 = (
    Get-FileHash -LiteralPath $BundleFile -Algorithm SHA256
).Hash.ToLowerInvariant()
$ChecksumLines = @(
    "$BundleSha256  $(Split-Path -Leaf $BundleFile)"
    "$EdSha256  $EdFile"
    "$VaeSha256  $VaeFile"
)
$ChecksumPath = Join-Path $ResolvedOutDir "SHA256SUMS.txt"
$ChecksumText = ($ChecksumLines -join "`n") + "`n"
[IO.File]::WriteAllText($ChecksumPath, $ChecksumText, [Text.Encoding]::ASCII)

Write-Output "OFFLINE ARTIFACTS VERIFIED"
Write-Output "Directory: $ResolvedOutDir"
Write-Output "Upload these four files:"
Write-Output "  $BundleFile"
Write-Output "  $EdPath"
Write-Output "  $VaePath"
Write-Output "  $ChecksumPath"
