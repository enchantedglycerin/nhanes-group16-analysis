param([string]$RepositoryName = 'nhanes-group16-analysis')
$ErrorActionPreference = 'Stop'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'Install GitHub CLI before publishing.'
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.git'))) {
    throw 'Publish from the initialized local repository, or initialize and commit the source files first.'
}
& gh auth status --hostname github.com
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub authentication is unavailable. Run: gh auth login --hostname github.com'
}
$tracked = @(& git -C $PSScriptRoot ls-files)
if ($LASTEXITCODE -ne 0) { throw 'Cannot read the local Git repository.' }
$allowed = @(Get-Content -Raw -Encoding UTF8 (Join-Path $PSScriptRoot 'source_files.json') | ConvertFrom-Json)
$unexpected = @($tracked | Where-Object { $_ -notin $allowed })
if ($unexpected.Count -gt 0 -or $tracked.Count -ne $allowed.Count) {
    throw 'Tracked files differ from source_files.json. Review the source list before publishing.'
}
$changes = @(& git -C $PSScriptRoot status --porcelain)
if ($LASTEXITCODE -ne 0 -or $changes.Count -gt 0) {
    throw 'Commit the current source changes before publishing.'
}
$remotes = @(& git -C $PSScriptRoot remote)
if ($remotes -contains 'origin') {
    throw 'An origin remote already exists. Inspect it with git remote -v before pushing.'
}
& gh repo create $RepositoryName --private --source $PSScriptRoot --remote origin --push `
    --description 'Python analysis, figures and Thai reports for NHANES Group 16'
if ($LASTEXITCODE -ne 0) { throw 'GitHub repository creation or push failed.' }
& gh repo view $RepositoryName --json url --jq .url
if ($LASTEXITCODE -ne 0) { throw 'Push finished, but the GitHub URL could not be verified.' }

