# Release Notes - CineRipR 1.0.35

## Major WebGUI Overhaul 🎉

This release brings **massive improvements** to the WebGUI with 4 highly requested features and a complete interface restructuring!

## New Features

### 1. 🔔 Toast Notifications
Real-time pop-up notifications for important events:
- Success notifications when archives are processed
- Error notifications when extraction fails
- Warning and info messages
- Auto-dismiss after 5 seconds
- Elegant slide-in animations

### 2. 📋 Processing Queue
See what's coming next:
- View all pending archives waiting for processing
- Real-time status updates (pending, processing, completed, failed)
- Archive count for each item
- Visual status indicators with color coding
- Empty state when queue is clear

### 3. 🔍 Log Filtering & Search
Find what you need instantly:
- Filter by log level (All, Errors, Warnings, Info, Debug)
- Full-text search through log history
- Combine filters and search for precise results
- Maintains last 100 log entries
- Real-time filtering without page refresh

### 4. 💻 System Health Monitoring
Keep an eye on disk space:
- Real-time disk usage for Downloads, Extracted, and Finished directories
- Visual progress bars with percentage
- Used/Free space display in GB
- Warning indicators when disk is > 90% full
- 7-Zip version information

## Interface Improvements

### Tab-Based Navigation
Clean, organized interface with 4 main sections:
- **📊 Overview**: Stats and current operation at a glance
- **📋 Queue**: Processing queue and upcoming work
- **💻 System Health**: Disk space and system information
- **📝 Logs**: Filtered and searchable log viewer

### Better Status Display
- Fixed inconsistency: "Status: Idle" with "Aktuelles Release: Processing..."
- Current release now clears when processing completes
- Status indicator syncs correctly with processing state
- Cleaner separation of concerns

### Visual Enhancements
- 🎨 Favicon with CineRipR branding (shows in browser tab)
- Responsive design for mobile and tablet
- Smooth tab transitions
- Less overwhelming, better organized layout
- Improved card designs and spacing

## Technical Details

### Backend Enhancements
- `StatusTracker` extended with queue management methods
- System health monitoring with disk usage calculations
- Notification system with read/unread tracking
- 7-Zip version detection
- Thread-safe operations for all new features

### API Endpoints
- `GET /api/status` - Enhanced with queue, health, and notifications
- `POST /api/notifications/<id>/read` - Mark notifications as read
- `GET /favicon.svg` - Serve embedded SVG favicon

### Frontend Architecture
- Single-page application with JavaScript-based tab switching
- No page reloads, smooth transitions
- Auto-refresh every 2 seconds
- Efficient DOM updates to prevent flickering
- Local state management for filters

## Usage

### Default View (Overview Tab)
Shows the most important information at a glance:
- Processing statistics
- Current operation and progress
- Status indicator

### Queue Tab
Monitor what's waiting to be processed:
- All pending releases
- Current processing status
- Archive counts per release

### System Health Tab
Keep your system healthy:
- Disk space monitoring
- Prevent out-of-space errors
- Know when to clean up

### Logs Tab
Debug and monitor:
- Filter by severity
- Search for specific messages
- Find issues quickly

## Upgrade Instructions

```bash
# Pull new image
docker pull ghcr.io/rokk001/cineripr:1.0.35
# or
docker pull ghcr.io/rokk001/cineripr:latest

# Restart container
docker-compose restart

# Open WebGUI
http://your-server:8080
```

No configuration changes needed - all features work automatically!

## Before & After

**Before:**
- Single page with everything mixed together
- No queue visibility
- Manual log searching
- No disk space monitoring
- Status inconsistencies

**After:**
- Clean tab-based navigation
- Dedicated queue view
- Powerful log filtering
- Real-time health monitoring
- Consistent status display
- Professional notifications

## Breaking Changes

None! Fully backwards compatible.

## Known Issues

- Queue only shows items discovered in current scan (not persisted across restarts)
- Notifications are in-memory only

## Coming Soon

These features are already planned:
- Manual control panel (pause/resume/force-run)
- Release detail view with file lists
- Timeline/history charts
- Config editor in WebGUI

---

Enjoy the new features! 🎬

