# Release Notes - CineRipR v1.0.36

**Release Date:** November 9, 2025

## 🎉 Major WebGUI Enhancement - Advanced Features Complete

This release completes the **comprehensive WebGUI overhaul** with the implementation of features 5-8, building upon the foundation laid in version 1.0.35. CineRipR now offers a **fully-featured, interactive dashboard** with advanced monitoring, control, and customization capabilities.

---

## ✨ New Features

### 🔍 Release Detail View (Feature 5)
Click on any item in the queue to view detailed information in a beautiful modal dialog:
- **Status & Metadata**: View release status, archive count, start time, and duration
- **Real-time Progress**: See which archive is currently being processed with live progress
- **Filtered Logs**: View logs specific to that release for easier troubleshooting
- **Keyboard Control**: Press ESC to close the modal quickly

### 📅 Timeline/History View (Feature 6)
New "History" tab provides a visual timeline of all processed releases:
- **Color-coded Timeline**: Green markers for successful releases, red for failures
- **Detailed Metrics**: Duration, archive count, completion time for each release
- **Smooth Animations**: Entries slide in with beautiful transitions
- **At-a-glance Status**: Quickly see your processing history over time

### 🎮 Manual Control Panel (Feature 7)
Take control of processing with pause/resume functionality:
- **Pause/Resume Buttons**: Beautiful gradient-styled control buttons
- **Visual Status Indicator**: Always know if processing is active or paused
- **Automatic Updates**: Button states update automatically based on processing status
- **Toast Notifications**: Get feedback when pausing or resuming

### 🌓 Dark/Light Mode Toggle (Feature 8)
Switch between themes with a single click:
- **Theme Toggle Button**: Convenient button in the header (🌙 for dark, ☀️ for light)
- **Persistent Preference**: Theme saved to localStorage and server
- **Smooth Transitions**: CSS animations for seamless theme switching
- **Full Theme System**: Complete CSS variable-based theming throughout the app
- **Optimized Colors**: Carefully chosen colors for both dark and light modes

### 💻 CPU & Memory Monitoring
Enhanced system health monitoring:
- **CPU Usage**: Real-time CPU percentage display
- **Memory Usage**: Current memory usage percentage
- **Auto-refresh**: Updated every 2 seconds alongside disk metrics
- **Visual Integration**: Seamlessly integrated into System Health tab

### 🔊 Toast Sound Notifications
Audio feedback for important events:
- **Different Tones**: Unique two-tone sounds for success, error, warning, and info
- **Web Audio API**: High-quality synthesized notification sounds
- **Configurable**: Enable/disable via localStorage (soundEnabled)
- **Automatic**: Plays on all toast notifications

---

## 🔧 Technical Improvements

### Backend Enhancements
- **Extended StatusTracker**: New `ReleaseHistory` dataclass for tracking processing history
- **Enhanced GlobalStatus**: Added `is_paused`, `history`, and `theme_preference` fields
- **New Methods**:
  - `add_to_history()` - Record completed releases
  - `set_theme()` / `get_theme()` - Theme preference management
  - `pause_processing()` / `resume_processing()` / `is_paused()` - Process control
- **System Health**: Enhanced `update_system_health()` with CPU and memory monitoring via psutil
- **New API Endpoints**:
  - `GET/POST /api/theme` - Theme management
  - `POST /api/control/pause` - Pause processing
  - `POST /api/control/resume` - Resume processing
  - `GET /api/history` - Retrieve processing history

### Frontend Architecture
- **Complete CSS Variable System**: Full theming support with CSS custom properties
- **Modular Modal System**: Reusable modal components with animations
- **Enhanced State Management**: Better tracking of queue data and theme preferences
- **Improved Responsiveness**: All new features work seamlessly on mobile devices
- **Keyboard Controls**: ESC key to close modals
- **Local Storage Integration**: Theme and sound preferences persist across sessions

---

## 📋 Complete Feature List (All 8 Features)

### Features 1-4 (Implemented in v1.0.35)
1. ✅ **Toast Notifications** - Real-time pop-up notifications
2. ✅ **Download-Queue Display** - Visual queue of pending archives
3. ✅ **Log Filtering & Search** - Advanced log management
4. ✅ **System Health Monitor** - Disk space monitoring

### Features 5-8 (Implemented in v1.0.36)
5. ✅ **Release Detail View** - Detailed modal for queue items
6. ✅ **Timeline/History View** - Visual processing history
7. ✅ **Manual Control Panel** - Pause/resume controls
8. ✅ **Dark/Light Mode Toggle** - Theme customization

---

## 🎨 Visual Enhancements

- **Improved Header**: Theme toggle button integrated into header design
- **Better Cards**: All components now use CSS variables for consistent theming
- **Enhanced Animations**: Smooth transitions for theme switching and modal interactions
- **Light Theme**: Beautiful light theme with optimized colors and contrast
- **Responsive Design**: All new features work perfectly on mobile and tablet devices

---

## 📦 Dependencies

- Python >= 3.11
- Flask >= 3.0.0
- psutil >= 5.9.0 (for CPU/memory monitoring)
- 7-Zip (official binary recommended for full RAR5 support)

---

## 🚀 Upgrade Instructions

### Using Docker

```bash
docker pull ghcr.io/rokk001/cineripr:1.0.36
# or
docker pull ghcr.io/rokk001/cineripr:latest
```

Then restart your container.

### Using pip

```bash
pip install --upgrade cineripr
```

---

## 🎯 What's Next?

With all 8 planned features now implemented, CineRipR has a **fully-featured, modern WebGUI**. Future updates may include:
- User preferences and settings management
- Advanced filtering and sorting options
- Export functionality for logs and history
- Multi-language support
- Plugin system for extensibility

---

## 🐛 Bug Reports & Feature Requests

Please report any issues or suggest new features on GitHub:
https://github.com/Rokk001/CineRipR/issues

---

## 👏 Acknowledgments

Thank you to all users who provided feedback and helped shape these features!

---

**Full Changelog**: https://github.com/Rokk001/CineRipR/blob/main/CHANGELOG.md

