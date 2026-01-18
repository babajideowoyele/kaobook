# PowerShell Script: Consolidate dissertation/data folders as git submodules
# This script automates the process of:
# 1. Backing up local folder contents
# 2. Removing the folder from git tracking
# 3. Adding the folder as a submodule from GitHub
# 4. Copying any new local files to the submodule

param(
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

# Configuration
$RepoRoot = "c:\Users\babaj\Documents\GitHub\kaobook"
$DataDir = "$RepoRoot\dissertation\data"
$BackupDir = "$RepoRoot\.backups\consolidation-$(Get-Date -Format 'yyyy-MM-dd-HHmmss')"
$GitHubUser = "babajideowoyele"

# Folders to consolidate (local folder name -> GitHub repo name)
$FoldersToConsolidate = @{
    "rolebox-crunchbase" = "rolebox-crunchbase"
    "rolebox-news" = "rolebox-news"
    "rolebox-websites" = "rolebox-websites"
}

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    $color = switch ($Type) {
        "Info" { "Cyan" }
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        default { "White" }
    }
    Write-Host "[$Type] $Message" -ForegroundColor $color
}

function Invoke-GitCommand {
    param([string]$Command, [string]$WorkDir = $RepoRoot)
    if ($DryRun) {
        Write-Status "[DRY RUN] Would execute: git $Command" -Type "Warning"
        return $true
    }

    Push-Location $WorkDir
    try {
        $output = Invoke-Expression "git $Command 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-Status "Git command failed: $output" -Type "Error"
            return $false
        }
        return $true
    }
    finally {
        Pop-Location
    }
}

function Backup-Folder {
    param([string]$FolderPath, [string]$FolderName)

    $backupPath = Join-Path $BackupDir $FolderName

    if ($DryRun) {
        Write-Status "[DRY RUN] Would backup: $FolderPath -> $backupPath" -Type "Warning"
        return $true
    }

    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }

    Write-Status "Backing up $FolderName to $backupPath"
    Copy-Item -Path $FolderPath -Destination $backupPath -Recurse -Force
    return $true
}

function Remove-FolderFromGit {
    param([string]$RelativePath)

    Write-Status "Removing $RelativePath from git tracking"

    # Remove from git index (keep files)
    if (-not (Invoke-GitCommand "rm -r --cached `"$RelativePath`"")) {
        return $false
    }

    return $true
}

function Add-Submodule {
    param([string]$RepoName, [string]$LocalPath)

    $repoUrl = "https://github.com/$GitHubUser/$RepoName.git"
    $relativePath = "dissertation/data/$RepoName"

    Write-Status "Adding submodule: $repoUrl -> $relativePath"

    if ($DryRun) {
        Write-Status "[DRY RUN] Would add submodule: $repoUrl" -Type "Warning"
        return $true
    }

    # Remove local folder first
    $fullPath = Join-Path $DataDir $RepoName
    if (Test-Path $fullPath) {
        Remove-Item -Path $fullPath -Recurse -Force
    }

    # Add submodule
    if (-not (Invoke-GitCommand "submodule add `"$repoUrl`" `"$relativePath`"")) {
        return $false
    }

    return $true
}

function Sync-NewFiles {
    param([string]$BackupPath, [string]$SubmodulePath)

    if (-not (Test-Path $BackupPath)) {
        Write-Status "No backup found at $BackupPath" -Type "Warning"
        return $true
    }

    Write-Status "Syncing new files from backup to submodule"

    if ($DryRun) {
        Write-Status "[DRY RUN] Would sync files from $BackupPath" -Type "Warning"
        return $true
    }

    # Get all files from backup
    $backupFiles = Get-ChildItem -Path $BackupPath -Recurse -File

    foreach ($file in $backupFiles) {
        $relativePath = $file.FullName.Substring($BackupPath.Length + 1)
        $targetPath = Join-Path $SubmodulePath $relativePath
        $targetDir = Split-Path $targetPath -Parent

        # Skip .git folder
        if ($relativePath -match "^\.git") {
            continue
        }

        # Check if file exists in submodule
        if (-not (Test-Path $targetPath)) {
            Write-Status "  Copying new file: $relativePath" -Type "Info"

            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }

            Copy-Item -Path $file.FullName -Destination $targetPath -Force
        }
    }

    return $true
}

function Process-Folder {
    param([string]$LocalName, [string]$RepoName)

    $localPath = Join-Path $DataDir $LocalName
    $relativePath = "dissertation/data/$LocalName"

    Write-Status "Processing: $LocalName" -Type "Info"
    Write-Host "  Local path: $localPath"
    Write-Host "  GitHub repo: $GitHubUser/$RepoName"

    # Check if folder exists
    if (-not (Test-Path $localPath)) {
        Write-Status "Folder not found: $localPath" -Type "Warning"
        return $true
    }

    # Check if already a submodule
    $gitmodulesPath = Join-Path $RepoRoot ".gitmodules"
    if (Test-Path $gitmodulesPath) {
        $gitmodules = Get-Content $gitmodulesPath -Raw
        if ($gitmodules -match [regex]::Escape($relativePath)) {
            Write-Status "Already a submodule: $LocalName" -Type "Warning"
            return $true
        }
    }

    # Step 1: Backup
    if (-not (Backup-Folder -FolderPath $localPath -FolderName $LocalName)) {
        return $false
    }

    # Step 2: Remove from git
    if (-not (Remove-FolderFromGit -RelativePath $relativePath)) {
        return $false
    }

    # Step 3: Add as submodule
    if (-not (Add-Submodule -RepoName $RepoName -LocalPath $localPath)) {
        return $false
    }

    # Step 4: Sync new files
    $backupPath = Join-Path $BackupDir $LocalName
    $submodulePath = Join-Path $DataDir $LocalName
    if (-not (Sync-NewFiles -BackupPath $backupPath -SubmodulePath $submodulePath)) {
        return $false
    }

    Write-Status "Successfully processed: $LocalName" -Type "Success"
    return $true
}

# Main execution
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Submodule Consolidation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Status "Running in DRY RUN mode - no changes will be made" -Type "Warning"
    Write-Host ""
}

# Show current status
Write-Status "Current submodules:"
Push-Location $RepoRoot
git submodule status 2>$null
Pop-Location
Write-Host ""

# Confirm before proceeding
if (-not $DryRun -and -not $Force) {
    Write-Host "This script will:" -ForegroundColor Yellow
    Write-Host "  1. Backup local folders to: $BackupDir"
    Write-Host "  2. Remove folders from git tracking"
    Write-Host "  3. Add them as submodules from GitHub"
    Write-Host "  4. Copy any new local files to the submodules"
    Write-Host ""
    $confirm = Read-Host "Continue? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Status "Aborted by user" -Type "Warning"
        exit 0
    }
}

# Process each folder
$success = $true
foreach ($entry in $FoldersToConsolidate.GetEnumerator()) {
    Write-Host ""
    if (-not (Process-Folder -LocalName $entry.Key -RepoName $entry.Value)) {
        Write-Status "Failed to process: $($entry.Key)" -Type "Error"
        $success = $false
        if (-not $Force) {
            break
        }
    }
}

Write-Host ""
if ($success) {
    Write-Status "Consolidation complete!" -Type "Success"

    if (-not $DryRun) {
        Write-Host ""
        Write-Status "Next steps:"
        Write-Host "  1. Review changes: git status"
        Write-Host "  2. Commit submodule changes in each submodule (if new files added)"
        Write-Host "  3. Push submodules: git push (in each submodule)"
        Write-Host "  4. Commit main repo: git add . && git commit -m 'Consolidate data folders as submodules'"
        Write-Host "  5. Push main repo: git push"
        Write-Host ""
        Write-Host "Backups saved to: $BackupDir" -ForegroundColor Cyan
    }
} else {
    Write-Status "Consolidation failed - check errors above" -Type "Error"
    if (-not $DryRun) {
        Write-Host "Backups available at: $BackupDir" -ForegroundColor Yellow
    }
}
