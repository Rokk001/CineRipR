# Release Notes - CineRipR v2.5.14

## Summary
This release includes several bug fixes and improvements to the processing pipeline, with a focus on stability and performance.

## Changes
- Fixed queue/history duplicates issue
- Resolved check interval problem
- Improved progress bar functionality
- Enhanced error handling in web interface
- Optimized performance for large file processing

## Bug Fixes
- Fixed AttributeError in template rendering
- Corrected TemplateNotFound errors
- Resolved JavaScript embedding issues causing 500 errors
- Fixed countdown-percentage reference in embedded JavaScript
- Addressed disk space calculation issues

## Improvements
- Better progress bar UX with redesign of Run Now button
- Enhanced UI with footer cleanup
- Improved performance optimizations
- Better handling of repeat modes and intervals
- Fixed next_run_time persistence issues

## Technical Details
- Updated web interface with Flask Blueprints separation
- Improved database integration for settings management
- Enhanced status tracking with thread-safe operations
- Fixed timestamp parsing for ISO format strings
- Added comprehensive logging throughout the application

## Compatibility
This release maintains backward compatibility with previous versions. No breaking changes are introduced.

## Installation
To install this release, please download from the GitHub releases page or use:
```
git clone https://github.com/Rokk001/CineRipR.git
cd CineRipR
git checkout v2.5.14
```

## Contributors
- Rokk001

## License
This project is licensed under the MIT License - see the LICENSE file for details.