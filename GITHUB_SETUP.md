# GitHub Repository Setup Guide

Follow these steps to create and push this project to GitHub under your account `stefan-bergstein`.

## Step 1: Initialize Git Repository (if not already done)

```bash
cd /Users/stefan/Projects/bob-test/strava
git init
```

## Step 2: Add All Files

```bash
git add .
```

## Step 3: Create Initial Commit

```bash
git commit -m "Initial commit: Strava to Komoot Activity Sync Tool

- Modular Python application for syncing Strava activities to Komoot
- Smart GPX export with fallback to activity streams
- Automatic sport type mapping
- Date range and activity type filtering
- Comprehensive CLI with download, sync, and list commands
- MIT License"
```

## Step 4: Create GitHub Repository

### Option A: Using GitHub CLI (gh)

If you have GitHub CLI installed:

```bash
gh repo create stefan-bergstein/strava-komoot-sync \
  --public \
  --description "Sync Strava activities to Komoot with smart GPX export and automatic sport type mapping" \
  --source=. \
  --push
```

### Option B: Using GitHub Web Interface

1. Go to https://github.com/new
2. Fill in the details:
   - **Owner**: stefan-bergstein
   - **Repository name**: `strava-komoot-sync`
   - **Description**: "Sync Strava activities to Komoot with smart GPX export and automatic sport type mapping"
   - **Visibility**: Public (or Private if you prefer)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
3. Click "Create repository"

## Step 5: Add Remote and Push (if using Option B)

```bash
git remote add origin https://github.com/stefan-bergstein/strava-komoot-sync.git
git branch -M main
git push -u origin main
```

## Step 6: Verify

Visit your repository at:
```
https://github.com/stefan-bergstein/strava-komoot-sync
```

## Repository Details

### Suggested Repository Name
`strava-komoot-sync`

### Suggested Description
"Sync Strava activities to Komoot with smart GPX export and automatic sport type mapping"

### Topics (Tags) to Add
After creating the repository, add these topics for better discoverability:
- `strava`
- `komoot`
- `gpx`
- `activity-sync`
- `python`
- `cycling`
- `running`
- `fitness`
- `api-client`

To add topics:
1. Go to your repository page
2. Click the gear icon next to "About"
3. Add the topics listed above

## Optional: Add Repository Badges

Add these badges to the top of your README.md:

```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
```

## Security Reminder

Before pushing, double-check that these files are NOT in your repository:
- ❌ `config.json`
- ❌ `strava_config.json`
- ❌ `.strava-app.key`
- ❌ `sync_log.json`
- ❌ `strava_data/` directory

These are already in `.gitignore`, but verify with:
```bash
git status
```

If any sensitive files appear, add them to `.gitignore` before committing.

## Post-Creation Steps

1. **Enable GitHub Pages** (optional) - for documentation
2. **Add repository description and website** in repository settings
3. **Create releases** when you have stable versions
4. **Add a CHANGELOG.md** to track version changes

## Troubleshooting

### If you get authentication errors:

**Using HTTPS:**
```bash
# You'll need a Personal Access Token
# Create one at: https://github.com/settings/tokens
git remote set-url origin https://YOUR_TOKEN@github.com/stefan-bergstein/strava-komoot-sync.git
```

**Using SSH (recommended):**
```bash
git remote set-url origin git@github.com:stefan-bergstein/strava-komoot-sync.git
```

### If the repository already exists:

```bash
git remote remove origin
git remote add origin https://github.com/stefan-bergstein/strava-komoot-sync.git
git push -u origin main