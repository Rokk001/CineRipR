# CineRipR Release 1.0.7 Creation Script
# This script creates a new release with proper tagging and documentation

param(
    [switch]$DryRun
)

$VERSION = "1.0.7"
$TAG = "v$VERSION"
$RELEASE_TITLE = "CineRipR $VERSION - Docker Permissions & .dctmp Support"

Write-Host "🚀 Creating CineRipR Release $VERSION" -ForegroundColor Green

# Check if we're in a git repository
try {
    $null = git rev-parse --git-dir
} catch {
    Write-Host "❌ Error: Not in a git repository" -ForegroundColor Red
    exit 1
}

# Check if working directory is clean
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "❌ Error: Working directory is not clean. Please commit or stash changes." -ForegroundColor Red
    Write-Host "Uncommitted changes:" -ForegroundColor Yellow
    Write-Host $gitStatus
    exit 1
}

# Check if tag already exists
try {
    $null = git rev-parse $TAG
    Write-Host "❌ Error: Tag $TAG already exists" -ForegroundColor Red
    exit 1
} catch {
    # Tag doesn't exist, which is good
}

Write-Host "✅ Pre-release checks passed" -ForegroundColor Green

if ($DryRun) {
    Write-Host "🔍 DRY RUN - Would create tag $TAG" -ForegroundColor Yellow
    Write-Host "Tag message would be:" -ForegroundColor Yellow
    Write-Host "Release $VERSION`n`n$RELEASE_TITLE`n`nThis patch release addresses critical Docker permission issues and adds support for .dctmp archive files.`n`nKey Changes:`n- Fixed Docker file permission problems (non-root user, proper umask)`n- Added .dctmp archive format support`n- Automatic permission correction after extraction`n- Enhanced Docker security and file handling`n`nSee RELEASE_NOTES_1.0.7.md for detailed information."
    exit 0
}

# Create and push the tag
Write-Host "📝 Creating tag $TAG..." -ForegroundColor Blue
$tagMessage = @"
Release $VERSION

$RELEASE_TITLE

This patch release addresses critical Docker permission issues and adds support for .dctmp archive files.

Key Changes:
- Fixed Docker file permission problems (non-root user, proper umask)
- Added .dctmp archive format support
- Automatic permission correction after extraction
- Enhanced Docker security and file handling

See RELEASE_NOTES_1.0.7.md for detailed information.
"@

git tag -a $TAG -m $tagMessage

Write-Host "📤 Pushing tag to remote..." -ForegroundColor Blue
git push origin $TAG

Write-Host "🎉 Release $VERSION created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Go to GitHub and create a release from tag $TAG"
Write-Host "2. Copy content from RELEASE_NOTES_1.0.7.md for the release description"
Write-Host "3. Build and push Docker image:"
Write-Host "   docker build -t ghcr.io/rokk001/cineripr:$VERSION ."
Write-Host "   docker push ghcr.io/rokk001/cineripr:$VERSION"
Write-Host "4. Update latest tag:"
Write-Host "   docker tag ghcr.io/rokk001/cineripr:$VERSION ghcr.io/rokk001/cineripr:latest"
Write-Host "   docker push ghcr.io/rokk001/cineripr:latest"
Write-Host ""
Write-Host "Release URL: https://github.com/Rokk001/CineRipR/releases/tag/$TAG" -ForegroundColor Cyan
