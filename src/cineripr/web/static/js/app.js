// Create particles
function createParticles() {
    const container = document.getElementById('particles');
    for (let i = 0; i < 25; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        container.appendChild(particle);
    }
}
createParticles();

// Tab switching
function switchTab(tabName) {
    document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.closest('.nav-tab').classList.add('active');
    document.getElementById('tab-' + tabName).classList.add('active');
    
    // Load settings when switching to settings tab (NEW in v2.2.0)
    if (tabName === 'settings') {
        loadSettings();
    }
}

// Toast notifications
let notificationQueue = new Set();
let soundEnabled = localStorage.getItem('soundEnabled') !== 'false';

// Simple notification sound using Web Audio API
function playNotificationSound(type) {
    if (!soundEnabled) return;
    
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Different frequencies for different notification types
        const frequencies = {
            success: [523.25, 659.25], // C5, E5
            error: [329.63, 261.63],    // E4, C4
            warning: [440, 440],        // A4, A4
            info: [523.25, 523.25]      // C5, C5
        };
        
        const freqs = frequencies[type] || frequencies.info;
        oscillator.frequency.value = freqs[0];
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
        
        // Second tone
        setTimeout(() => {
            const osc2 = audioContext.createOscillator();
            const gain2 = audioContext.createGain();
            osc2.connect(gain2);
            gain2.connect(audioContext.destination);
            osc2.frequency.value = freqs[1];
            gain2.gain.setValueAtTime(0.1, audioContext.currentTime);
            gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            osc2.start(audioContext.currentTime);
            osc2.stop(audioContext.currentTime + 0.1);
        }, 100);
    } catch (e) {
        console.log('Sound notification not supported');
    }
}

function showToast(type, title, message, duration = 5000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type]}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    // Play sound
    playNotificationSound(type);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Log filtering
let logFilter = 'all';
let logSearchTerm = '';

document.getElementById('log-filter').addEventListener('change', (e) => {
    logFilter = e.target.value;
    filterLogs();
});

document.getElementById('log-search').addEventListener('input', (e) => {
    logSearchTerm = e.target.value.toLowerCase();
    filterLogs();
});

function filterLogs() {
    const logs = document.querySelectorAll('.log-entry');
    logs.forEach(log => {
        const level = log.dataset.level;
        const text = log.textContent.toLowerCase();
        
        const levelMatch = logFilter === 'all' || level === logFilter;
        const searchMatch = logSearchTerm === '' || text.includes(logSearchTerm);
        
        log.classList.toggle('hidden', !(levelMatch && searchMatch));
    });
}

let previousStatus = {};
let currentQueueData = [];

// Modal functions
function openReleaseModal(index) {
    const item = currentQueueData[index];
    if (!item) return;
    
    document.getElementById('modal-title').textContent = item.name;
    document.getElementById('modal-status').innerHTML = `<span class="status-badge ${item.status}">${item.status}</span>`;
    document.getElementById('modal-archive-count').textContent = item.archive_count || 0;
    
    // Start time and duration
    if (item.start_time) {
        const startTime = new Date(item.start_time);
        document.getElementById('modal-start-time').textContent = startTime.toLocaleString('de-DE');
        
        const now = new Date();
        const duration = Math.floor((now - startTime) / 1000);
        const hours = Math.floor(duration / 3600);
        const minutes = Math.floor((duration % 3600) / 60);
        const seconds = duration % 60;
        document.getElementById('modal-duration').textContent = 
            `${hours}h ${minutes}m ${seconds}s`;
    } else {
        document.getElementById('modal-start-time').textContent = 'Not started';
        document.getElementById('modal-duration').textContent = '-';
    }
    
    // Progress
    if (item.status === 'processing' && item.current_archive) {
        document.getElementById('modal-progress-section').style.display = 'block';
        document.getElementById('modal-current-archive').textContent = item.current_archive;
        const progress = item.progress || 0;
        document.getElementById('modal-progress-fill').style.width = progress + '%';
    } else {
        document.getElementById('modal-progress-section').style.display = 'none';
    }
    
    // Logs (filter by release name if available in logs)
    const logsContainer = document.getElementById('modal-logs');
    const allLogs = previousStatus.recent_logs || [];
    const releaseLogs = allLogs.filter(log => 
        log.message.includes(item.name) || 
        (item.current_archive && log.message.includes(item.current_archive))
    );
    
    if (releaseLogs.length > 0) {
        logsContainer.innerHTML = releaseLogs.slice().reverse().map(log => {
            const time = new Date(log.timestamp).toLocaleTimeString('de-DE');
            const level = (log.level || 'info').toLowerCase();
            return `<div class="modal-log-entry ${level}">[${time}] [${log.level}] ${log.message}</div>`;
        }).join('');
    } else {
        logsContainer.innerHTML = '<div style="text-align: center; color: rgba(255, 255, 255, 0.4); padding: 20px;">No specific logs for this release</div>';
    }
    
    document.getElementById('release-modal').classList.add('active');
}

function closeModal(event) {
    if (!event || event.target.classList.contains('modal-overlay')) {
        document.getElementById('release-modal').classList.remove('active');
    }
}

// Keyboard shortcut to close modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal({ target: { classList: { contains: () => true } } });
    }
});

// Control functions
function pauseProcessing() {
    fetch('/api/control/pause', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            showToast('warning', 'Processing Paused', 'Processing has been paused');
        })
        .catch(err => {
            showToast('error', 'Error', 'Failed to pause processing');
            console.error('Pause error:', err);
        });
}

function resumeProcessing() {
    fetch('/api/control/resume', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            showToast('success', 'Processing Resumed', 'Processing has been resumed');
        })
        .catch(err => {
            showToast('error', 'Error', 'Failed to resume processing');
            console.error('Resume error:', err);
        });
}

// NEW in v2.1.0: Trigger run now
function triggerRunNow() {
    if (confirm('⚠️ Start processing now and skip wait?')) {
        fetch('/api/control/trigger-now', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                showToast('success', 'Run Triggered', 'Starting processing now...', true);
                // Hide countdown progressbar immediately
                document.getElementById('countdown-container').style.display = 'none';
            })
            .catch(err => {
                showToast('error', 'Error', 'Failed to trigger run');
                console.error('Trigger error:', err);
            });
    }
}

// NEW in v2.2.5: Handle header control button
function handleHeaderControl() {
    const btn = document.getElementById('header-control-btn');
    
    if (btn.classList.contains('run-now')) {
        triggerRunNow();
    } else if (btn.classList.contains('pause')) {
        pauseProcessing();
    } else if (btn.classList.contains('resume')) {
        resumeProcessing();
    }
}

// Settings Management (NEW in v2.2.0)
function loadSettings() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(data => {
            // Scheduling
            // Default: repeat_forever = true
            document.getElementById('setting-repeat-forever').checked = data.repeat_forever !== false;
            // Default: repeat_after_minutes = 30
            document.getElementById('setting-repeat-minutes').value = data.repeat_after_minutes !== undefined ? data.repeat_after_minutes : 30;
            
            // Retention
            // Default: finished_retention_days = 15
            document.getElementById('setting-retention-days').value = data.finished_retention_days !== undefined ? data.finished_retention_days : 15;
            // Default: enable_delete = false
            document.getElementById('setting-enable-delete').checked = data.enable_delete === true;
            
            // Subfolders
            // Default: include_sample = false
            document.getElementById('setting-include-sample').checked = data.include_sample === true;
            // Default: include_sub = true
            document.getElementById('setting-include-sub').checked = data.include_sub !== false;
            // Default: include_other = false
            document.getElementById('setting-include-other').checked = data.include_other === true;
            
            // UI Preferences
            // Default: toast_notifications = true
            document.getElementById('setting-toast-notifications').checked = data.toast_notifications !== false;
            // Default: toast_sound = false
            document.getElementById('setting-toast-sound').checked = data.toast_sound === true;
            
            // File Processing
            // Default: file_stability_hours = 24
            document.getElementById('setting-file-stability-hours').value = data.file_stability_hours !== undefined ? data.file_stability_hours : 24;
            
            // Advanced
            // Default: demo_mode = false
            document.getElementById('setting-demo-mode').checked = data.demo_mode === true;
        })
        .catch(err => {
            console.error('Failed to load settings:', err);
            showToast('error', 'Error', 'Failed to load settings');
        });
}

function saveAllSettings() {
    const settings = {
        repeat_forever: document.getElementById('setting-repeat-forever').checked,
        repeat_after_minutes: parseInt(document.getElementById('setting-repeat-minutes').value),
        finished_retention_days: parseInt(document.getElementById('setting-retention-days').value),
        enable_delete: document.getElementById('setting-enable-delete').checked,
        include_sample: document.getElementById('setting-include-sample').checked,
        include_sub: document.getElementById('setting-include-sub').checked,
        include_other: document.getElementById('setting-include-other').checked,
        toast_notifications: document.getElementById('setting-toast-notifications').checked,
        toast_sound: document.getElementById('setting-toast-sound').checked,
        file_stability_hours: parseInt(document.getElementById('setting-file-stability-hours').value),
        demo_mode: document.getElementById('setting-demo-mode').checked,
    };
    
    // Validation
    if (settings.repeat_after_minutes < 1 || settings.repeat_after_minutes > 1440) {
        showToast('error', 'Validation Error', 'Check interval must be between 1 and 1440 minutes');
        return;
    }
    if (settings.finished_retention_days < 1 || settings.finished_retention_days > 365) {
        showToast('error', 'Validation Error', 'Retention days must be between 1 and 365');
        return;
    }
    if (settings.file_stability_hours < 1 || settings.file_stability_hours > 168) {
        showToast('error', 'Validation Error', 'File stability hours must be between 1 and 168 (7 days)');
        return;
    }
    
    // Save each setting
    const promises = Object.entries(settings).map(([key, value]) => 
        fetch(`/api/settings/${key}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value })
        })
    );
    
    Promise.all(promises)
        .then(() => {
            showToast('success', 'Settings Saved', 'All settings have been saved successfully', true);
            const statusEl = document.getElementById('settings-status');
            statusEl.textContent = '✅ Settings saved successfully! Changes will take effect on next run.';
            statusEl.className = 'settings-status success';
            statusEl.style.display = 'block';
            setTimeout(() => statusEl.style.display = 'none', 5000);
        })
        .catch(err => {
            console.error('Failed to save settings:', err);
            showToast('error', 'Save Failed', 'Failed to save some settings');
            const statusEl = document.getElementById('settings-status');
            statusEl.textContent = '❌ Failed to save settings. Please try again.';
            statusEl.className = 'settings-status error';
            statusEl.style.display = 'block';
        });
}

function resetSettings() {
    if (confirm('⚠️ Reset all settings to default values? This cannot be undone.')) {
        // Reset to defaults (from DEFAULT_SETTINGS)
        const defaults = {
            repeat_forever: true,
            repeat_after_minutes: 30,
            finished_retention_days: 15,
            enable_delete: false,
            include_sample: false,
            include_sub: true,
            include_other: false,
            toast_notifications: true,
            toast_sound: false,
            file_stability_hours: 24,
            demo_mode: false,
        };
        
        const promises = Object.entries(defaults).map(([key, value]) => 
            fetch(`/api/settings/${key}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value })
            })
        );
        
        Promise.all(promises)
            .then(() => {
                loadSettings(); // Reload to show defaults
                showToast('success', 'Settings Reset', 'All settings have been reset to defaults', true);
            })
            .catch(err => {
                console.error('Failed to reset settings:', err);
                showToast('error', 'Reset Failed', 'Failed to reset settings');
            });
    }
}

// Theme toggle
let currentTheme = 'dark';

function toggleTheme() {
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    
    // Save to server
    fetch('/api/theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: newTheme })
    }).catch(err => console.error('Failed to save theme:', err));
}

function applyTheme(theme) {
    currentTheme = theme;
    const body = document.body;
    const icon = document.getElementById('theme-icon');
    
    if (theme === 'light') {
        body.classList.add('light-theme');
        icon.textContent = '☀️';
    } else {
        body.classList.remove('light-theme');
        icon.textContent = '🌙';
    }
    
    localStorage.setItem('theme', theme);
}

// Load theme preference
function loadThemePreference() {
    // First check localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    }
    
    // Then fetch from server
    fetch('/api/theme')
        .then(r => r.json())
        .then(data => {
            if (data.theme && data.theme !== currentTheme) {
                applyTheme(data.theme);
            }
        })
        .catch(err => console.error('Failed to load theme:', err));
}

loadThemePreference();

function updateStatus() {
    fetch('/api/status')
        .then(r => r.json())
        .then(data => {
            // Stats
            updateValue('processed', data.processed_count || 0);
            updateValue('failed', data.failed_count || 0);
            updateValue('unsupported', data.unsupported_count || 0);
            updateValue('deleted', data.deleted_count || 0);
            updateValue('extracted', data.extracted_count || 0);
            updateValue('copied', data.copied_count || 0);
            updateValue('moved', data.moved_count || 0);
            
            // Notifications
            if (previousStatus.processed_count !== undefined) {
                if (data.processed_count > previousStatus.processed_count) {
                    showToast('success', 'Success', `${data.processed_count - previousStatus.processed_count} archive(s) processed`);
                }
                if (data.failed_count > previousStatus.failed_count) {
                    showToast('error', 'Error', `${data.failed_count - previousStatus.failed_count} archive(s) failed`);
                }
            }
            
            // Status
            const isRunning = data.is_running || false;
            const isPaused = data.is_paused || false;
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('status-text');
            
            if (isPaused) {
                statusDot.classList.remove('running');
                statusText.textContent = 'Paused';
            } else if (isRunning) {
                statusDot.classList.add('running');
                statusText.textContent = 'Processing';
            } else {
                statusDot.classList.remove('running');
                statusText.textContent = 'Idle';
            }
            
            // Countdown Progressbar (NEW in v2.5.0)
            const countdownContainer = document.getElementById('countdown-container');
            const countdownFill = document.getElementById('countdown-fill');
            const countdownPercentage = document.getElementById('countdown-percentage');
            const countdownTime = document.getElementById('countdown-time');
            
            const isIdle = !isRunning && !isPaused;
            const hasNextRun = data.seconds_until_next_run !== null && data.seconds_until_next_run >= 0;
            // CRITICAL FIX v2.5.5: Show progressbar if repeat mode is enabled, even if seconds_until_next_run is null
            const hasRepeatMode = data.repeat_mode && data.repeat_interval_minutes > 0;
            
            if (isIdle && (hasNextRun || hasRepeatMode)) {
                // Show countdown progressbar
                countdownContainer.style.display = 'flex';
                
                // Calculate percentage (inverse: 100% = just finished, 0% = starting now)
                const totalSeconds = (data.repeat_interval_minutes || 30) * 60;
                // If seconds_until_next_run is null but repeat mode is active, show 100% (just started)
                const remainingSeconds = data.seconds_until_next_run !== null ? data.seconds_until_next_run : totalSeconds;
                const percentage = Math.max(0, Math.min(100, (remainingSeconds / totalSeconds) * 100));
                
                // Update progressbar
                countdownFill.style.width = percentage + '%';
                countdownPercentage.textContent = Math.round(percentage) + '%';
                
                // Format time
                const hours = Math.floor(remainingSeconds / 3600);
                const minutes = Math.floor((remainingSeconds % 3600) / 60);
                const seconds = remainingSeconds % 60;
                
                let timeString;
                if (hours > 0) {
                    timeString = `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                } else {
                    timeString = `${minutes}:${String(seconds).padStart(2, '0')}`;
                }
                countdownTime.textContent = timeString;
                
                // Color based on time remaining
                if (percentage < 20) {
                    countdownFill.style.background = 'linear-gradient(90deg, #ef4444 0%, #dc2626 100%)'; // Red
                } else if (percentage < 50) {
                    countdownFill.style.background = 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)'; // Orange
                } else {
                    countdownFill.style.background = 'linear-gradient(90deg, var(--accent-color) 0%, rgba(139, 92, 246, 0.7) 100%)'; // Purple
                }
            } else if (isIdle) {
                // Idle but no next run (manual mode)
                countdownContainer.style.display = 'none';
                statusText.textContent = 'Idle (Manual Mode)';
            } else {
                // Processing or Paused
                countdownContainer.style.display = 'none';
            }
            
            // Control panel (REMOVED in v2.2.5 - replaced by header button)
            // Legacy code removed
            
            // Current operation
            const release = data.current_release;
            if (release && isRunning) {
                document.getElementById('release-name').textContent = release.release_name || '-';
                document.getElementById('archive-name').textContent = release.current_archive || '-';
                document.getElementById('status-message').textContent = release.message || '-';
                
                const progress = release.archive_total > 0 
                    ? Math.round((release.archive_progress / release.archive_total) * 100) : 0;
                
                document.getElementById('progress-fill').style.width = progress + '%';
                document.getElementById('progress-text').textContent = progress + '%';
            } else {
                document.getElementById('release-name').textContent = '-';
                document.getElementById('archive-name').textContent = '-';
                document.getElementById('status-message').textContent = isRunning ? 'Initializing...' : 'Waiting for files...';
                document.getElementById('progress-fill').style.width = '0%';
                document.getElementById('progress-text').textContent = '0%';
            }
            
            // Queue
            const queue = data.queue || [];
            currentQueueData = queue; // Store for modal access
            const queueList = document.getElementById('queue-list');
            if (queue.length === 0) {
                queueList.innerHTML = '<div class="queue-empty">No items in queue</div>';
            } else {
                queueList.innerHTML = queue.map((item, index) => `
                    <div class="queue-item" onclick="openReleaseModal(${index})">
                        <div class="queue-dot ${item.status}"></div>
                        <div class="queue-info">
                            <div class="queue-name">${item.name}</div>
                            <div class="queue-meta">${item.archive_count} archive(s) • ${item.status}</div>
                        </div>
                    </div>
                `).join('');
            }
            
            // System health
            if (data.system_health) {
                const h = data.system_health;
                updateDisk('downloads', h.disk_downloads_used_gb, h.disk_downloads_free_gb, h.disk_downloads_percent);
                updateDisk('extracted', h.disk_extracted_used_gb, h.disk_extracted_free_gb, h.disk_extracted_percent);
                updateDisk('finished', h.disk_finished_used_gb, h.disk_finished_free_gb, h.disk_finished_percent);
                document.getElementById('seven-zip-version').textContent = h.seven_zip_version || 'Unknown';
                document.getElementById('cpu-usage').textContent = (h.cpu_percent || 0).toFixed(1) + '%';
                document.getElementById('memory-usage').textContent = (h.memory_percent || 0).toFixed(1) + '%';
            }
            
            // Logs
            const logsContainer = document.getElementById('logs-container');
            const currentScroll = logsContainer.scrollTop;
            const isBottom = logsContainer.scrollHeight - logsContainer.clientHeight <= currentScroll + 10;
            
            if (data.recent_logs && data.recent_logs.length > 0) {
                logsContainer.innerHTML = data.recent_logs.slice().reverse().map(log => {
                    const time = new Date(log.timestamp).toLocaleTimeString('de-DE');
                    const level = (log.level || 'info').toLowerCase();
                    return `<div class="log-entry ${level}" data-level="${level}">[${time}] [${log.level}] ${log.message}</div>`;
                }).join('');
                
                filterLogs();
                
                if (isBottom) {
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                }
            }
            
            // History
            const history = data.history || [];
            const historyTimeline = document.getElementById('history-timeline');
            if (history.length === 0) {
                historyTimeline.innerHTML = `
                    <div class="history-empty">
                        <div class="history-empty-icon">🕐</div>
                        <div style="font-size: 1.2em; margin-bottom: 10px;">No history yet</div>
                        <div>Processed releases will appear here</div>
                    </div>
                `;
            } else {
                historyTimeline.innerHTML = history.map(item => {
                    const endTime = new Date(item.timestamp);
                    const timeStr = endTime.toLocaleString('en-US');
                    const duration = item.duration_seconds || 0;
                    const hours = Math.floor(duration / 3600);
                    const minutes = Math.floor((duration % 3600) / 60);
                    const seconds = Math.floor(duration % 60);
                    const durationStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m ${seconds}s`;
                    
                    const isSuccess = item.status === 'completed';
                    const markerClass = isSuccess ? 'success' : 'failed';
                    const borderColor = isSuccess ? '#10b981' : '#ef4444';
                    
                    return `
                        <div class="timeline-item">
                            <div class="timeline-marker ${markerClass}"></div>
                            <div class="timeline-content" style="--timeline-color: ${borderColor}">
                                <div class="timeline-header">
                                    <div class="timeline-title">${item.release_name}</div>
                                    <div class="timeline-time">${timeStr}</div>
                                </div>
                                <div class="timeline-meta">
                                    <div class="timeline-meta-item">
                                        <span>⏱</span> ${durationStr}
                                    </div>
                                    <div class="timeline-meta-item">
                                        <span>📦</span> Processed: ${item.processed_archives || 0} | Failed: ${item.failed_archives || 0}
                                    </div>
                                    <div class="timeline-meta-item">
                                        <span>${isSuccess ? '✓' : '✗'}</span> ${isSuccess ? 'Completed' : 'Failed'}
                                    </div>
                                </div>
                                ${item.error_messages && item.error_messages.length > 0 ? `
                                <div class="timeline-errors">
                                    <div style="color: #ef4444; font-weight: 600; margin-bottom: 5px;">⚠️ Errors:</div>
                                    ${item.error_messages.slice(0, 3).map(err => `<div style="font-size: 0.85em; opacity: 0.8;">• ${err}</div>`).join('')}
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            // Update time
            if (data.last_update) {
                document.getElementById('last-update').textContent = new Date(data.last_update).toLocaleString('de-DE');
            }
            
            // Next Run Countdown (NEW in v2.1.0)
            const nextRunCard = document.getElementById('next-run-card');
            if (data.repeat_mode && data.seconds_until_next_run !== null && !isRunning) {
                const seconds = data.seconds_until_next_run;
                
                if (seconds > 0) {
                    nextRunCard.style.display = 'block';
                    
                    const hours = Math.floor(seconds / 3600);
                    const minutes = Math.floor((seconds % 3600) / 60);
                    const secs = seconds % 60;
                    
                    const timeStr = hours > 0 
                        ? `${hours}h ${minutes}m ${secs}s`
                        : minutes > 0
                            ? `${minutes}m ${secs}s`
                            : `${secs}s`;
                    
                    document.getElementById('next-run-countdown').textContent = timeStr;
                    
                    if (data.next_run_time) {
                        const nextRunDate = new Date(data.next_run_time);
                        document.getElementById('next-run-text').textContent = 
                            `at ${nextRunDate.toLocaleTimeString('de-DE')}`;
                    }
                    
                    const countdownEl = document.getElementById('next-run-countdown');
                    if (seconds < 60) {
                        countdownEl.classList.add('pulse');
                    } else {
                        countdownEl.classList.remove('pulse');
                    }
                } else if (seconds === 0) {
                    nextRunCard.style.display = 'block';
                    document.getElementById('next-run-countdown').textContent = 'Starting now...';
                    document.getElementById('next-run-text').textContent = '';
                }
            } else {
                nextRunCard.style.display = 'none';
            }
            
            previousStatus = data;
        })
        .catch(err => console.error('Error:', err));
}

function updateValue(id, value) {
    const el = document.getElementById(id);
    if (el.textContent != value) {
        el.style.transform = 'scale(1.15)';
        setTimeout(() => {
            el.textContent = value;
            el.style.transform = 'scale(1)';
        }, 150);
    }
}

function updateDisk(name, used, free, percent) {
    document.getElementById(`disk-${name}-used`).textContent = `${used.toFixed(1)} GB used`;
    document.getElementById(`disk-${name}-free`).textContent = `${free.toFixed(1)} GB free`;
    document.getElementById(`disk-${name}-percent`).textContent = `${percent.toFixed(1)}%`;
    
    const fill = document.getElementById(`disk-${name}-fill`);
    fill.style.width = `${percent}%`;
    fill.classList.toggle('warning', percent > 90);
}

// Initial load and auto-refresh
// FIX v2.5.5: Ensure only ONE interval runs, use 2s as shown in footer
(function() {
    let statusInterval = null;
    function startStatusUpdates() {
        if (statusInterval) {
            clearInterval(statusInterval); // Clear any existing interval
        }
        updateStatus(); // Initial call
        statusInterval = setInterval(updateStatus, 2000); // 2 seconds as shown in footer
    }
    startStatusUpdates();
})();