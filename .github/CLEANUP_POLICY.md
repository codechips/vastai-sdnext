# Docker Registry Cleanup Policy

This document describes our simplified automated cleanup policy for the GitHub Container Registry.

## Overview

We use a simple, consistent cleanup policy that runs after every Docker build to maintain exactly 3 versions.

## Build & Cleanup Schedule

### **Automatic Build & Cleanup**
- **Triggers**: 
  - Push to main branch (immediate builds for your changes)
  - Weekly schedule (Sunday 2 AM UTC for upstream SD.Next updates)
  - Manual dispatch
- **Process**: Build → Push → Clean up old versions
- **Keeps**: Exactly 3 most recent tagged versions
- **Integration**: Cleanup is part of the build workflow

## Image Tagging Strategy

Our images are tagged with:
- `latest` - Always points to the most recent build
- `YYYYMMDD` - Date-based tags for all builds
- `YYYY-WUU` - Week-based tags for scheduled builds (e.g., 2024-W52)

## Retention Rules

| Image Type | Retention Policy |
|------------|------------------|
| All tagged versions | Keep exactly 3 most recent |
| Untagged versions | Automatically removed |
| Latest tag | Always kept (points to most recent) |

## Manual Intervention

To manually trigger a build (which includes cleanup):

1. Go to Actions → "Weekly Build & Cleanup"
2. Click "Run workflow"
3. Monitor the build and cleanup results

## Monitoring

Each build generates a summary report that includes:
- Build trigger type (push vs weekly)
- Image tags created
- Cleanup results (3 versions retained)
- Any errors encountered

## Build Types

### **Push Builds** (Code Changes)
- **Trigger**: When you push to main branch
- **Tags**: `latest`, `YYYYMMDD`
- **Purpose**: Immediate builds for repository changes

### **Weekly Builds** (Upstream Updates)
- **Trigger**: Every Sunday at 2 AM UTC
- **Tags**: `latest`, `YYYYMMDD`, `YYYY-WUU`
- **Purpose**: Catch upstream SD.Next changes

## Benefits

This simplified strategy provides:
- **Predictable**: Always exactly 3 versions available
- **Simple**: One workflow handles build + cleanup
- **Responsive**: Immediate builds on code changes
- **Current**: Weekly builds catch upstream updates
- **Clean**: No complex retention policies to manage

## Emergency Procedures

If you need to preserve specific versions:
1. Tag them with a semantic version (e.g., `v1.0.0`) before they're cleaned up
2. Or manually download them before the next build
3. Contact maintainers to adjust retention if needed

The 3-version limit provides adequate rollback capability while keeping the registry clean.