# Docker Registry Cleanup Policy

This document describes our automated cleanup policies for the GitHub Container Registry.

## Overview

We use automated cleanup workflows to manage storage costs and keep our registry organized. The cleanup runs at different intervals with varying aggressiveness.

## Cleanup Schedules

### 1. **Regular Cleanup** (Weekly)
- **When**: Every Sunday at 2:00 AM UTC
- **What**: Removes old versions while keeping recent ones
- **Keeps**: Last 5 tagged versions
- **Also runs**: After each successful Docker build

### 2. **Deep Cleanup** (Monthly)
- **When**: 1st of each month at 3:00 AM UTC
- **What**: More aggressive cleanup of old versions
- **Keeps**: Last 3 tagged versions minimum
- **Special**: Removes all untagged versions older than 7 days

### 3. **Manual Cleanup** (On-demand)
- **When**: Triggered manually via GitHub Actions
- **Options**: 
  - Standard cleanup
  - Aggressive cleanup (keeps only 2 versions)
- **Use case**: Emergency storage management

## Image Tagging Strategy

Our images are tagged with:
- `latest` - Always points to the most recent build
- `YYYYMMDD-sha` - Date + commit SHA for tracking
- `YYYYMMDD` - Daily builds for easy reference
- `main` - Branch-based tags

## Retention Rules

| Image Type | Retention Period | Minimum Kept |
|------------|-----------------|--------------|
| Tagged (latest) | Always kept | 1 |
| Tagged (dated) | 30 days | 3-5 |
| Tagged (SHA) | 14 days | 2-3 |
| Untagged | 7 days | 1 |

## Manual Intervention

To manually trigger cleanup:

1. Go to Actions → "Cleanup Docker Images"
2. Click "Run workflow"
3. Choose cleanup type
4. Monitor the results

To trigger aggressive cleanup:

1. Go to Actions → "Deep Registry Cleanup"
2. Click "Run workflow"
3. Check "Aggressive cleanup" if needed
4. Review the analysis before proceeding

## Monitoring

Each cleanup run generates a summary report that includes:
- Number of versions before/after
- Space saved
- Versions retained
- Any errors encountered

## Emergency Procedures

If you need to preserve specific versions:

1. Tag them with a semantic version (e.g., `v1.0.0`)
2. Or download them locally before cleanup
3. Contact maintainers to adjust retention policy

## Cost Optimization

This cleanup strategy helps us:
- Stay within GitHub's free tier limits
- Reduce bandwidth costs
- Improve registry performance
- Maintain a clean version history