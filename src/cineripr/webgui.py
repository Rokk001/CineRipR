"""WebGUI for CineRipR status monitoring."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify, render_template_string

from .status import get_status_tracker

_LOGGER = logging.getLogger(__name__)

# Favicon SVG (embedded)
FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="100" height="100" rx="20" fill="url(#grad1)"/>
  <text x="50" y="70" font-size="60" text-anchor="middle" fill="white">🎬</text>
</svg>'''

# HTML Template - wird weiter unten definiert
HTML_TEMPLATE = """
<!-- HTML Template wird hier eingefügt -->
"""

# Jetzt das eigentliche HTML Template laden
from pathlib import Path
import os

# Da das Template sehr groß ist, lade ich es aus einer separaten Funktion
def get_html_template() -> str:
    return '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CineRipR - Dashboard</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #e9ecef;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Animated Background */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            opacity: 0.3;
        }
        
        .particle {
            position: absolute;
            width: 3px;
            height: 3px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            animation: float 20s infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); }
            25% { transform: translateY(-100px) translateX(50px); }
            50% { transform: translateY(-50px) translateX(-50px); }
            75% { transform: translateY(-150px) translateX(100px); }
        }
        
        /* Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }
        
        /* Header */
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .header-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .header-icon {
            font-size: 3em;
            animation: rotate3d 3s ease-in-out infinite;
        }
        
        @keyframes rotate3d {
            0%, 100% { transform: rotateY(0deg); }
            50% { transform: rotateY(180deg); }
        }
        
        .header-text h1 {
            font-size: 2em;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 5px;
        }
        
        .header-text .subtitle {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.9em;
        }
        
        .header-status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #6b7280;
        }
        
        .status-dot.running {
            background: #10b981;
            animation: pulse 2s infinite;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.6);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }
        
        /* Navigation Tabs */
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 10px;
        }
        
        .nav-tab {
            flex: 1;
            padding: 12px 20px;
            background: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.95em;
            font-weight: 500;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .nav-tab:hover {
            background: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.9);
        }
        
        .nav-tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        /* Tab Content */
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Cards */
        .card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .card h2 {
            color: #fff;
            margin-bottom: 20px;
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .stat-card {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 20px;
            border-left: 3px solid var(--color);
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }
        
        .stat-label {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: 700;
            color: var(--color);
        }
        
        .stat-card.success { --color: #10b981; }
        .stat-card.error { --color: #ef4444; }
        .stat-card.warning { --color: #f59e0b; }
        .stat-card.info { --color: #3b82f6; }
        
        /* Progress */
        .progress-section {
            margin-top: 20px;
        }
        
        .progress-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 0.9em;
        }
        
        .progress-bar {
            height: 30px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            background-size: 200% 100%;
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        /* Queue */
        .queue-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .queue-item {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .queue-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        
        .queue-dot.pending { background: #6b7280; }
        .queue-dot.processing {
            background: #10b981;
            animation: pulse 2s infinite;
        }
        .queue-dot.completed { background: #3b82f6; }
        .queue-dot.failed { background: #ef4444; }
        
        .queue-info {
            flex: 1;
        }
        
        .queue-name {
            color: #fff;
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .queue-meta {
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.5);
        }
        
        .queue-empty {
            text-align: center;
            padding: 40px;
            color: rgba(255, 255, 255, 0.4);
        }
        
        /* System Health */
        .disk-grid {
            display: grid;
            gap: 20px;
        }
        
        .disk-item {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 20px;
        }
        
        .disk-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
        }
        
        .disk-label {
            color: #fff;
            font-weight: 500;
        }
        
        .disk-percent {
            color: rgba(255, 255, 255, 0.7);
            font-weight: 600;
        }
        
        .disk-bar {
            height: 10px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .disk-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
            transition: width 0.5s;
            border-radius: 5px;
        }
        
        .disk-fill.warning {
            background: linear-gradient(90deg, #f59e0b 0%, #ef4444 100%);
        }
        
        .disk-stats {
            display: flex;
            justify-content: space-between;
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.5);
        }
        
        /* Logs */
        .log-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .log-filter, .log-search {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 8px 12px;
            color: #fff;
            font-size: 0.9em;
        }
        
        .log-filter {
            cursor: pointer;
        }
        
        .log-search {
            flex: 1;
        }
        
        .log-search:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .logs-container {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 10px;
            padding: 15px;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        
        .log-entry {
            padding: 8px 10px;
            margin-bottom: 8px;
            border-left: 3px solid transparent;
            border-radius: 4px;
            background: rgba(0, 0, 0, 0.2);
        }
        
        .log-entry.info { border-left-color: #3b82f6; }
        .log-entry.warning { border-left-color: #f59e0b; }
        .log-entry.error { border-left-color: #ef4444; }
        .log-entry.debug { border-left-color: #6b7280; }
        
        .log-entry.hidden { display: none; }
        
        /* Toast */
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 350px;
        }
        
        .toast {
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-left: 4px solid var(--toast-color);
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.3s ease-out;
            display: flex;
            gap: 12px;
        }
        
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .toast.success { --toast-color: #10b981; }
        .toast.error { --toast-color: #ef4444; }
        .toast.warning { --toast-color: #f59e0b; }
        .toast.info { --toast-color: #3b82f6; }
        
        .toast-icon {
            font-size: 20px;
        }
        
        .toast-content {
            flex: 1;
        }
        
        .toast-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .toast-message {
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .toast-close {
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.5);
            cursor: pointer;
            font-size: 18px;
            padding: 0;
        }
        
        .toast-close:hover {
            color: #fff;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 20px;
            color: rgba(255, 255, 255, 0.4);
            font-size: 0.85em;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
            }
            
            .nav-tabs {
                flex-wrap: wrap;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .log-controls {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    <div class="toast-container" id="toast-container"></div>
    
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-left">
                <div class="header-icon">🎬</div>
                <div class="header-text">
                    <h1>CineRipR</h1>
                    <div class="subtitle">Archive Extraction Dashboard</div>
                </div>
            </div>
            <div class="header-status">
                <div class="status-dot" id="status-dot"></div>
                <div id="status-text">Idle</div>
            </div>
        </div>
        
        <!-- Navigation -->
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="switchTab('overview')">
                📊 Overview
            </button>
            <button class="nav-tab" onclick="switchTab('queue')">
                📋 Queue
            </button>
            <button class="nav-tab" onclick="switchTab('health')">
                💻 System Health
            </button>
            <button class="nav-tab" onclick="switchTab('logs')">
                📝 Logs
            </button>
        </div>
        
        <!-- Overview Tab -->
        <div class="tab-content active" id="tab-overview">
            <!-- Stats -->
            <div class="card">
                <h2>📈 Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-card success">
                        <div class="stat-label">✓ Verarbeitet</div>
                        <div class="stat-value" id="processed">0</div>
                    </div>
                    <div class="stat-card error">
                        <div class="stat-label">✗ Fehlgeschlagen</div>
                        <div class="stat-value" id="failed">0</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-label">⚠ Nicht unterstützt</div>
                        <div class="stat-value" id="unsupported">0</div>
                    </div>
                    <div class="stat-card info">
                        <div class="stat-label">🗑 Gelöscht</div>
                        <div class="stat-value" id="deleted">0</div>
                    </div>
                </div>
            </div>
            
            <!-- Current Operation -->
            <div class="card">
                <h2>⚙️ Current Operation</h2>
                <div id="current-operation-content">
                    <div class="progress-info">
                        <span><strong>Release:</strong> <span id="release-name">-</span></span>
                        <span id="progress-text">0%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill" style="width: 0%">0%</div>
                    </div>
                    <div class="progress-section">
                        <div style="margin-top: 15px; color: rgba(255, 255, 255, 0.7);">
                            <strong>Archiv:</strong> <span id="archive-name">-</span>
                        </div>
                        <div style="margin-top: 8px; color: rgba(255, 255, 255, 0.6); font-size: 0.9em;" id="status-message">
                            -
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Queue Tab -->
        <div class="tab-content" id="tab-queue">
            <div class="card">
                <h2>📋 Processing Queue</h2>
                <div class="queue-list" id="queue-list">
                    <div class="queue-empty">No items in queue</div>
                </div>
            </div>
        </div>
        
        <!-- System Health Tab -->
        <div class="tab-content" id="tab-health">
            <div class="card">
                <h2>💻 Disk Space</h2>
                <div class="disk-grid">
                    <div class="disk-item">
                        <div class="disk-header">
                            <div class="disk-label">📥 Downloads</div>
                            <div class="disk-percent" id="disk-downloads-percent">0%</div>
                        </div>
                        <div class="disk-bar">
                            <div class="disk-fill" id="disk-downloads-fill"></div>
                        </div>
                        <div class="disk-stats">
                            <span id="disk-downloads-used">0 GB used</span>
                            <span id="disk-downloads-free">0 GB free</span>
                        </div>
                    </div>
                    
                    <div class="disk-item">
                        <div class="disk-header">
                            <div class="disk-label">📦 Extracted</div>
                            <div class="disk-percent" id="disk-extracted-percent">0%</div>
                        </div>
                        <div class="disk-bar">
                            <div class="disk-fill" id="disk-extracted-fill"></div>
                        </div>
                        <div class="disk-stats">
                            <span id="disk-extracted-used">0 GB used</span>
                            <span id="disk-extracted-free">0 GB free</span>
                        </div>
                    </div>
                    
                    <div class="disk-item">
                        <div class="disk-header">
                            <div class="disk-label">✅ Finished</div>
                            <div class="disk-percent" id="disk-finished-percent">0%</div>
                        </div>
                        <div class="disk-bar">
                            <div class="disk-fill" id="disk-finished-fill"></div>
                        </div>
                        <div class="disk-stats">
                            <span id="disk-finished-used">0 GB used</span>
                            <span id="disk-finished-free">0 GB free</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🔧 System Information</h2>
                <div style="padding: 15px; background: rgba(0, 0, 0, 0.2); border-radius: 10px;">
                    <div style="margin-bottom: 10px;">
                        <strong>7-Zip Version:</strong> <span id="seven-zip-version">Unknown</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Logs Tab -->
        <div class="tab-content" id="tab-logs">
            <div class="card">
                <h2>📝 Logs</h2>
                <div class="log-controls">
                    <select class="log-filter" id="log-filter">
                        <option value="all">All Levels</option>
                        <option value="error">Errors</option>
                        <option value="warning">Warnings</option>
                        <option value="info">Info</option>
                        <option value="debug">Debug</option>
                    </select>
                    <input type="text" class="log-search" id="log-search" placeholder="Search logs...">
                </div>
                <div class="logs-container" id="logs-container"></div>
            </div>
        </div>
        
        <div class="footer">
            <span style="display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite;"></span>
            Last update: <span id="last-update">-</span> | Auto-refresh every 2 seconds
        </div>
    </div>
    
    <script>
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
        }
        
        // Toast notifications
        let notificationQueue = new Set();
        
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
        
        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    // Stats
                    updateValue('processed', data.processed_count || 0);
                    updateValue('failed', data.failed_count || 0);
                    updateValue('unsupported', data.unsupported_count || 0);
                    updateValue('deleted', data.deleted_count || 0);
                    
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
                    const statusDot = document.getElementById('status-dot');
                    const statusText = document.getElementById('status-text');
                    
                    if (isRunning) {
                        statusDot.classList.add('running');
                        statusText.textContent = 'Processing';
                    } else {
                        statusDot.classList.remove('running');
                        statusText.textContent = 'Idle';
                    }
                    
                    // Current operation
                    const release = data.current_release;
                    if (release && isRunning) {
                        document.getElementById('release-name').textContent = release.release_name || '-';
                        document.getElementById('archive-name').textContent = release.current_archive || '-';
                        document.getElementById('status-message').textContent = release.message || '-';
                        
                        const progress = release.archive_total > 0 
                            ? Math.round((release.archive_progress / release.archive_total) * 100) : 0;
                        
                        document.getElementById('progress-fill').style.width = progress + '%';
                        document.getElementById('progress-fill').textContent = progress + '%';
                        document.getElementById('progress-text').textContent = progress + '%';
                    } else {
                        document.getElementById('release-name').textContent = '-';
                        document.getElementById('archive-name').textContent = '-';
                        document.getElementById('status-message').textContent = isRunning ? 'Initializing...' : 'Waiting for files...';
                        document.getElementById('progress-fill').style.width = '0%';
                        document.getElementById('progress-fill').textContent = '0%';
                        document.getElementById('progress-text').textContent = '0%';
                    }
                    
                    // Queue
                    const queue = data.queue || [];
                    const queueList = document.getElementById('queue-list');
                    if (queue.length === 0) {
                        queueList.innerHTML = '<div class="queue-empty">No items in queue</div>';
                    } else {
                        queueList.innerHTML = queue.map(item => `
                            <div class="queue-item">
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
                    
                    // Update time
                    if (data.last_update) {
                        document.getElementById('last-update').textContent = new Date(data.last_update).toLocaleString('de-DE');
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
        updateStatus();
        setInterval(updateStatus, 2000);
    </script>
</body>
</html>'''


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    tracker = get_status_tracker()

    @app.route("/")
    def index() -> str:
        """Serve the main dashboard page."""
        return render_template_string(get_html_template())

    @app.route("/favicon.svg")
    def favicon() -> Any:
        """Serve the favicon."""
        return FAVICON_SVG, 200, {'Content-Type': 'image/svg+xml'}

    @app.route("/api/status")
    def api_status() -> Any:
        """Get current status as JSON."""
        status = tracker.get_status()
        return jsonify(status.to_dict())

    @app.route("/api/notifications/<notif_id>/read", methods=["POST"])
    def mark_notification_read(notif_id: str) -> Any:
        """Mark a notification as read."""
        tracker.mark_notification_read(notif_id)
        return jsonify({"status": "ok"})

    @app.route("/api/health")
    def api_health() -> Any:
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "cineripr-webgui"})

    return app


def run_webgui(host: str = "0.0.0.0", port: int = 8080, debug: bool = False) -> None:
    """Run the WebGUI server."""
    try:
        app = create_app()
        _LOGGER.info(f"Starting WebGUI on http://{host}:{port}")
        app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
    except OSError as exc:
        if "Address already in use" in str(exc) or "address is already in use" in str(exc):
            _LOGGER.error(f"Port {port} is already in use. Try a different port with --webgui-port")
        else:
            _LOGGER.error(f"Failed to start WebGUI: {exc}", exc_info=True)
        raise
    except Exception as exc:
        _LOGGER.error(f"Failed to start WebGUI: {exc}", exc_info=True)
        raise


__all__ = ["create_app", "run_webgui"]
