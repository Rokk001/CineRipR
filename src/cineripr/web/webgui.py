"""WebGUI for CineRipR status monitoring."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify, render_template_string, request

from .. import __version__
from .settings_db import get_settings_db
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
        
        :root {
            /* Dark Theme (default) */
            --bg-gradient-start: #1a1a2e;
            --bg-gradient-mid: #16213e;
            --bg-gradient-end: #0f3460;
            --text-primary: #e9ecef;
            --text-secondary: rgba(255, 255, 255, 0.7);
            --text-muted: rgba(255, 255, 255, 0.5);
            --card-bg: rgba(255, 255, 255, 0.05);
            --card-border: rgba(255, 255, 255, 0.1);
            --glass-bg: rgba(255, 255, 255, 0.05);
            --modal-bg: rgba(26, 26, 46, 0.98);
            --input-bg: rgba(0, 0, 0, 0.3);
            --stat-bg: rgba(0, 0, 0, 0.2);
        }
        
        body.light-theme {
            /* Light Theme */
            --bg-gradient-start: #f0f4f8;
            --bg-gradient-mid: #d9e2ec;
            --bg-gradient-end: #bcccdc;
            --text-primary: #1a202c;
            --text-secondary: rgba(26, 32, 44, 0.8);
            --text-muted: rgba(26, 32, 44, 0.6);
            --card-bg: rgba(255, 255, 255, 0.7);
            --card-border: rgba(0, 0, 0, 0.1);
            --glass-bg: rgba(255, 255, 255, 0.7);
            --modal-bg: rgba(255, 255, 255, 0.98);
            --input-bg: rgba(255, 255, 255, 0.5);
            --stat-bg: rgba(255, 255, 255, 0.5);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-mid) 50%, var(--bg-gradient-end) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            transition: all 0.3s ease;
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
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
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
            color: var(--text-muted);
            font-size: 0.9em;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .theme-toggle {
            width: 50px;
            height: 50px;
            border: none;
            border-radius: 12px;
            background: var(--stat-bg);
            color: var(--text-primary);
            font-size: 24px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .theme-toggle:hover {
            transform: scale(1.1) rotate(15deg);
        }
        
        .header-status {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Header Countdown (NEW in v2.2.5) */
        .header-countdown {
            margin-left: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85em;
            color: var(--text-secondary);
        }
        
        .header-countdown-separator {
            opacity: 0.3;
            margin: 0 5px;
        }
        
        .header-countdown-label {
            opacity: 0.7;
        }
        
        .header-countdown-time {
            font-family: 'Courier New', monospace;
            font-weight: 600;
            color: var(--accent-color);
            min-width: 50px;
        }
        
        .header-countdown-time.pulse {
            animation: pulse 1s ease-in-out infinite;
        }
        
        /* Header Control Button (NEW in v2.2.5) */
        .header-control-btn {
            margin-left: 10px;
            padding: 6px 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .header-control-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .header-control-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .header-control-btn.run-now {
            background: rgba(99, 102, 241, 0.2);
            border-color: rgba(99, 102, 241, 0.4);
            color: var(--accent-color);
        }
        
        .header-control-btn.pause {
            background: rgba(245, 158, 11, 0.2);
            border-color: rgba(245, 158, 11, 0.4);
            color: #fbbf24;
        }
        
        .header-control-btn.resume {
            background: rgba(16, 185, 129, 0.2);
            border-color: rgba(16, 185, 129, 0.4);
            color: #10b981;
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
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 10px;
        }
        
        .nav-tab {
            flex: 1;
            padding: 12px 20px;
            background: transparent;
            border: none;
            color: var(--text-muted);
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
            background: var(--input-bg);
            color: var(--text-secondary);
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
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
        }
        
        .card h2 {
            color: var(--text-primary);
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
            background: var(--stat-bg);
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
            color: var(--text-muted);
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
            background: var(--stat-bg);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .queue-item:hover {
            background: var(--input-bg);
            transform: translateX(5px);
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
            color: var(--text-primary);
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .queue-meta {
            font-size: 0.85em;
            color: var(--text-muted);
        }
        
        .queue-empty {
            text-align: center;
            padding: 40px;
            color: var(--text-muted);
        }
        
        /* System Health */
        .disk-grid {
            display: grid;
            gap: 20px;
        }
        
        .disk-item {
            background: var(--stat-bg);
            border-radius: 12px;
            padding: 20px;
        }
        
        .disk-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
        }
        
        .disk-label {
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .disk-percent {
            color: var(--text-secondary);
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
            background: var(--input-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 8px 12px;
            color: var(--text-primary);
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
        
        .footer a:hover {
            color: rgba(255, 255, 255, 0.9) !important;
        }
        
        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
            z-index: 10000;
            display: none;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.2s ease-out;
        }
        
        .modal-overlay.active {
            display: flex;
        }
        
        .modal {
            background: var(--modal-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            max-width: 900px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            animation: slideUp 0.3s ease-out;
        }
        
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .modal-header {
            padding: 30px 30px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-title {
            font-size: 1.8em;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .modal-close {
            background: rgba(255, 255, 255, 0.1);
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            color: #fff;
            font-size: 24px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .modal-close:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: rotate(90deg);
        }
        
        .modal-body {
            padding: 30px;
        }
        
        .modal-section {
            margin-bottom: 30px;
        }
        
        .modal-section-title {
            font-size: 1.2em;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .modal-detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            background: var(--stat-bg);
            border-radius: 12px;
            padding: 20px;
        }
        
        .modal-detail-item {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .modal-detail-label {
            color: var(--text-muted);
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .modal-detail-value {
            color: var(--text-primary);
            font-weight: 500;
            font-size: 1.1em;
        }
        
        .modal-logs {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 10px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        
        .modal-log-entry {
            padding: 6px 8px;
            margin-bottom: 6px;
            border-left: 3px solid transparent;
            border-radius: 4px;
            background: rgba(0, 0, 0, 0.2);
        }
        
        .modal-log-entry.info { border-left-color: #3b82f6; }
        .modal-log-entry.warning { border-left-color: #f59e0b; }
        .modal-log-entry.error { border-left-color: #ef4444; }
        .modal-log-entry.debug { border-left-color: #6b7280; }
        
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-badge.pending {
            background: rgba(107, 114, 128, 0.3);
            color: #9ca3af;
        }
        
        .status-badge.processing {
            background: rgba(16, 185, 129, 0.3);
            color: #10b981;
        }
        
        .status-badge.completed {
            background: rgba(59, 130, 246, 0.3);
            color: #3b82f6;
        }
        
        .status-badge.failed {
            background: rgba(239, 68, 68, 0.3);
            color: #ef4444;
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
        
        /* Timeline */
        .timeline {
            position: relative;
            padding: 20px 0;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 30px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(180deg, rgba(102, 126, 234, 0.5) 0%, rgba(118, 75, 162, 0.5) 100%);
        }
        
        .timeline-item {
            position: relative;
            padding-left: 70px;
            margin-bottom: 30px;
            animation: slideInLeft 0.5s ease-out;
        }
        
        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .timeline-marker {
            position: absolute;
            left: 20px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            border: 3px solid rgba(26, 26, 46, 1);
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.3);
        }
        
        .timeline-marker.success {
            background: #10b981;
            box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.3);
        }
        
        .timeline-marker.failed {
            background: #ef4444;
            box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.3);
        }
        
        .timeline-content {
            background: var(--stat-bg);
            border-radius: 12px;
            padding: 20px;
            border-left: 3px solid var(--timeline-color);
            transition: all 0.3s;
        }
        
        .timeline-content:hover {
            background: var(--input-bg);
            transform: translateX(5px);
        }
        
        .timeline-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .timeline-title {
            font-size: 1.1em;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .timeline-time {
            font-size: 0.85em;
            color: var(--text-muted);
        }
        
        .timeline-meta {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 0.9em;
            color: var(--text-secondary);
        }
        
        .timeline-meta-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .history-empty {
            text-align: center;
            padding: 60px 20px;
            color: rgba(255, 255, 255, 0.4);
        }
        
        .history-empty-icon {
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        /* Control Panel */
        .control-panel {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .control-btn {
            padding: 15px 25px;
            border: none;
            border-radius: 12px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
        
        .control-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
        }
        
        .control-btn:active {
            transform: translateY(0);
        }
        
        .control-btn.pause {
            background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
            color: white;
        }
        
        .control-btn.resume {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        
        .control-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .control-status {
            margin-top: 15px;
            padding: 12px;
            background: var(--stat-bg);
            border-radius: 8px;
            text-align: center;
            color: var(--text-secondary);
        }
        
        .control-status.paused {
            background: rgba(245, 158, 11, 0.2);
            border: 1px solid rgba(245, 158, 11, 0.4);
            color: #fbbf24;
        }
        
        /* Next Run Display (NEW in v2.1.0) */
        .next-run-display {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            padding: 20px;
        }
        
        .countdown-time {
            font-size: 2.5em;
            font-weight: bold;
            color: var(--accent-color);
            font-family: 'Courier New', monospace;
            text-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
            letter-spacing: 0.05em;
        }
        
        .countdown-time.pulse {
            animation: pulse 1s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.05); }
        }
        
        .countdown-text {
            font-size: 1.1em;
            color: var(--text-secondary);
            font-style: italic;
        }
        
        .control-btn.trigger {
            background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-hover) 100%);
            color: white;
            margin-top: 10px;
            width: 200px;
        }
        
        /* Settings Tab (NEW in v2.2.0) */
        .settings-categories {
            display: flex;
            flex-direction: column;
            gap: 30px;
        }
        
        .settings-category {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
        }
        
        .settings-category h3 {
            margin: 0 0 20px 0;
            color: var(--accent-color);
            font-size: 1.2em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .settings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .setting-item {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .setting-label {
            color: var(--text-primary);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            user-select: none;
        }
        
        .setting-label input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: var(--accent-color);
        }
        
        .setting-input {
            padding: 12px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1em;
            transition: all 0.3s;
        }
        
        .setting-input:focus {
            outline: none;
            border-color: var(--accent-color);
            background: rgba(255, 255, 255, 0.08);
        }
        
        .setting-help {
            font-size: 0.85em;
            color: var(--text-secondary);
            margin: 0;
        }
        
        .settings-actions {
            display: flex;
            gap: 15px;
            margin-top: 30px;
            flex-wrap: wrap;
        }
        
        .settings-status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            font-weight: 500;
            text-align: center;
        }
        
        .settings-status.success {
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: #10b981;
        }
        
        .settings-status.error {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #ef4444;
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
            
            .timeline::before {
                left: 15px;
            }
            
            .timeline-item {
                padding-left: 50px;
            }
            
            .timeline-marker {
                left: 5px;
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
                    <div class="subtitle">Archive Extraction Dashboard <span style="opacity: 0.6; font-size: 0.9em;">v{{ version }}</span></div>
                </div>
            </div>
            <div class="header-right">
                <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()">
                    <span id="theme-icon">🌙</span>
                </button>
                <div class="header-status">
                    <div class="status-dot" id="status-dot"></div>
                    <div id="status-text">Idle</div>
                    <!-- Countdown im Header (nur bei Idle + repeat_mode) -->
                    <div class="header-countdown" id="header-countdown" style="display: none;">
                        <span class="header-countdown-separator">|</span>
                        <span class="header-countdown-label">Next:</span>
                        <span class="header-countdown-time" id="header-countdown-time">--:--</span>
                    </div>
                    <!-- Dynamischer Control Button -->
                    <button class="header-control-btn" id="header-control-btn" onclick="handleHeaderControl()" style="display: none;">
                        <span id="header-control-icon">⏭️</span>
                    </button>
                </div>
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
            <button class="nav-tab" onclick="switchTab('history')">
                📅 History
            </button>
            <button class="nav-tab" onclick="switchTab('logs')">
                📝 Logs
            </button>
            <button class="nav-tab" onclick="switchTab('settings')">
                ⚙️ Settings
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
                    <div style="margin-bottom: 15px;">
                        <div style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 5px;">Release</div>
                        <div style="color: var(--text-primary); font-weight: 500; font-size: 1.1em;" id="release-name">-</div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <div style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 5px;">
                            Progress: <span id="progress-text" style="color: var(--text-primary); font-weight: 600;">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="progress-section">
                        <div style="margin-bottom: 10px;">
                            <div style="color: var(--text-muted); font-size: 0.9em; margin-bottom: 5px;">Current Archive</div>
                            <div style="color: var(--text-primary); font-weight: 500;" id="archive-name">-</div>
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.9em;" id="status-message">
                            Waiting for files...
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Next Run Countdown (NEW in v2.1.0) -->
            <div class="card" id="next-run-card" style="display: none;">
                <h2>⏰ Next Run</h2>
                <div class="next-run-display">
                    <div class="countdown-time" id="next-run-countdown">--:--:--</div>
                    <div class="countdown-text" id="next-run-text">Calculating...</div>
                    <button class="control-btn trigger" onclick="triggerRunNow()">
                        <span>⏭️</span> Run Now
                    </button>
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
                <div style="padding: 15px; background: var(--stat-bg); border-radius: 10px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px;">CineRipR Version</div>
                            <div style="color: var(--text-primary); font-weight: 500; font-size: 1.1em;" id="cineripr-version">{{ version }}</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px;">7-Zip Version</div>
                            <div style="color: var(--text-primary); font-weight: 500; font-size: 1.1em;" id="seven-zip-version">Unknown</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px;">CPU Usage</div>
                            <div style="color: var(--text-primary); font-weight: 500; font-size: 1.1em;" id="cpu-usage">0%</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.85em; margin-bottom: 5px;">Memory Usage</div>
                            <div style="color: var(--text-primary); font-weight: 500; font-size: 1.1em;" id="memory-usage">0%</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- History Tab -->
        <div class="tab-content" id="tab-history">
            <div class="card">
                <h2>📅 Processing History</h2>
                <div class="timeline" id="history-timeline">
                    <div class="history-empty">
                        <div class="history-empty-icon">🕐</div>
                        <div style="font-size: 1.2em; margin-bottom: 10px;">No history yet</div>
                        <div>Processed releases will appear here</div>
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
        
        <!-- Settings Tab (NEW in v2.2.0) -->
        <div class="tab-content" id="tab-settings">
            <div class="card">
                <h2>⚙️ Settings</h2>
                <p style="color: var(--text-secondary); margin-bottom: 25px;">
                    Configure CineRipR directly from the WebGUI. Changes are saved immediately and take effect on the next run.
                </p>
                
                <!-- Settings Categories -->
                <div class="settings-categories">
                    <!-- Scheduling -->
                    <div class="settings-category">
                        <h3>🕐 Scheduling</h3>
                        <div class="settings-grid">
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="setting-repeat-forever" />
                                    <span>Enable Auto-Run (Repeat Forever)</span>
                                </label>
                                <p class="setting-help">Automatically run processing in intervals</p>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">Check Interval (minutes)</label>
                                <input type="number" id="setting-repeat-minutes" min="1" max="1440" class="setting-input" />
                                <p class="setting-help">Time between automatic runs (1-1440 minutes)</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Retention -->
                    <div class="settings-category">
                        <h3>🗑️ Retention & Cleanup</h3>
                        <div class="settings-grid">
                            <div class="setting-item">
                                <label class="setting-label">Retention Days</label>
                                <input type="number" id="setting-retention-days" min="1" max="365" class="setting-input" />
                                <p class="setting-help">Days to keep files in finished directory</p>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="setting-enable-delete" />
                                    <span>Enable Automatic Deletion</span>
                                </label>
                                <p class="setting-help">⚠️ Automatically delete files after retention period</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Subfolders -->
                    <div class="settings-category">
                        <h3>📂 Subfolder Processing</h3>
                        <div class="settings-grid">
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="setting-include-sample" />
                                    <span>Include Sample Directories</span>
                                </label>
                                <p class="setting-help">Process 'Sample' folders (preview videos)</p>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="setting-include-sub" />
                                    <span>Include Subtitle Directories</span>
                                </label>
                                <p class="setting-help">Process 'Subs'/'Sub' folders</p>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="setting-include-other" />
                                    <span>Include Other Subdirectories</span>
                                </label>
                                <p class="setting-help">Process other folders (Proof, extras, etc.)</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- UI Preferences -->
                    <div class="settings-category">
                        <h3>🎨 UI Preferences</h3>
                        <div class="settings-grid">
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="setting-toast-notifications" />
                                    <span>Enable Toast Notifications</span>
                                </label>
                                <p class="setting-help">Show pop-up notifications for events</p>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="setting-toast-sound" />
                                    <span>Enable Notification Sounds</span>
                                </label>
                                <p class="setting-help">Play sound with notifications</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- File Processing -->
                    <div class="settings-category">
                        <h3>📁 File Processing</h3>
                        <div class="settings-grid">
                            <div class="setting-item">
                                <label class="setting-label">File Stability Hours</label>
                                <input type="number" id="setting-file-stability-hours" min="1" max="168" class="setting-input" />
                                <p class="setting-help">Hours an already extracted file (e.g., MKV) must be unchanged before processing. Only applies to non-archive files. Archives are processed immediately. (default: 24)</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Advanced -->
                    <div class="settings-category">
                        <h3>🔧 Advanced</h3>
                        <div class="settings-grid">
                            <div class="setting-item">
                                <label class="setting-label">
                                    <input type="checkbox" id="setting-demo-mode" />
                                    <span>Demo Mode</span>
                                </label>
                                <p class="setting-help">⚠️ Simulate operations without making changes</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="settings-actions">
                    <button class="control-btn" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);" onclick="saveAllSettings()">
                        <span>💾</span> Save All Settings
                    </button>
                    <button class="control-btn" style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);" onclick="resetSettings()">
                        <span>🔄</span> Reset to Defaults
                    </button>
                </div>
                
                <div id="settings-status" class="settings-status" style="display: none;"></div>
            </div>
        </div>
        
        <div class="footer">
            <div style="display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite;"></span>
                    Last update: <span id="last-update">-</span>
                </div>
                <div>Auto-refresh every 2 seconds</div>
                <div>CineRipR v{{ version }}</div>
                <div>
                    <a href="https://github.com/Rokk001/CineRipR" target="_blank" rel="noopener noreferrer" style="color: rgba(255, 255, 255, 0.6); text-decoration: none; display: flex; align-items: center; gap: 6px; transition: color 0.3s;">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" style="flex-shrink: 0;">
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                        </svg>
                        GitHub
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Release Detail Modal -->
    <div class="modal-overlay" id="release-modal" onclick="closeModal(event)">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2 class="modal-title" id="modal-title">Release Details</h2>
                <button class="modal-close" onclick="closeModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="modal-section">
                    <div class="modal-section-title">📋 Information</div>
                    <div class="modal-detail-grid">
                        <div class="modal-detail-item">
                            <div class="modal-detail-label">Status</div>
                            <div class="modal-detail-value" id="modal-status">-</div>
                        </div>
                        <div class="modal-detail-item">
                            <div class="modal-detail-label">Archive Count</div>
                            <div class="modal-detail-value" id="modal-archive-count">-</div>
                        </div>
                        <div class="modal-detail-item">
                            <div class="modal-detail-label">Start Time</div>
                            <div class="modal-detail-value" id="modal-start-time">-</div>
                        </div>
                        <div class="modal-detail-item">
                            <div class="modal-detail-label">Duration</div>
                            <div class="modal-detail-value" id="modal-duration">-</div>
                        </div>
                    </div>
                </div>
                
                <div class="modal-section" id="modal-progress-section" style="display: none;">
                    <div class="modal-section-title">📊 Progress</div>
                    <div style="background: rgba(0, 0, 0, 0.3); border-radius: 12px; padding: 20px;">
                        <div style="margin-bottom: 10px; font-size: 0.9em; color: rgba(255, 255, 255, 0.7);">
                            <strong>Current:</strong> <span id="modal-current-archive">-</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="modal-progress-fill" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
                
                <div class="modal-section">
                    <div class="modal-section-title">📝 Logs</div>
                    <div class="modal-logs" id="modal-logs">
                        <div style="text-align: center; color: rgba(255, 255, 255, 0.4); padding: 20px;">
                            No logs available for this release
                        </div>
                    </div>
                </div>
            </div>
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
                        // Hide countdown immediately
                        document.getElementById('next-run-card').style.display = 'none';
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
                    
                    // Header Countdown & Control Button (NEW in v2.2.5)
                    const headerCountdown = document.getElementById('header-countdown');
                    const headerCountdownTime = document.getElementById('header-countdown-time');
                    const headerControlBtn = document.getElementById('header-control-btn');
                    const headerControlIcon = document.getElementById('header-control-icon');
                    
                    if (isPaused) {
                        // Paused: Resume Button, kein Countdown
                        headerCountdown.style.display = 'none';
                        headerControlBtn.style.display = 'flex';
                        headerControlBtn.classList.remove('run-now', 'pause');
                        headerControlBtn.classList.add('resume');
                        headerControlIcon.textContent = '▶';
                        headerControlBtn.title = 'Resume Processing';
                    } else if (isRunning) {
                        // Running: Pause Button + Countdown (if available)
                        headerControlBtn.style.display = 'flex';
                        headerControlBtn.classList.remove('run-now', 'resume');
                        headerControlBtn.classList.add('pause');
                        headerControlIcon.textContent = '⏸';
                        headerControlBtn.title = 'Pause Processing';
                        
                        // Show countdown if available (for next scheduled run)
                        if (data.seconds_until_next_run !== null && data.seconds_until_next_run > 0) {
                            headerCountdown.style.display = 'flex';
                            
                            const seconds = data.seconds_until_next_run;
                            const hours = Math.floor(seconds / 3600);
                            const minutes = Math.floor((seconds % 3600) / 60);
                            const secs = seconds % 60;
                            
                            const timeStr = hours > 0 
                                ? `${hours}h ${minutes}m`
                                : minutes > 0
                                    ? `${minutes}m ${secs}s`
                                    : `${secs}s`;
                            
                            headerCountdownTime.textContent = timeStr;
                            
                            // Pulse if < 1 minute
                            if (seconds < 60) {
                                headerCountdownTime.classList.add('pulse');
                            } else {
                                headerCountdownTime.classList.remove('pulse');
                            }
                        } else {
                            headerCountdown.style.display = 'none';
                        }
                    } else {
                        // Idle: Countdown + Run Now Button (immer wenn next_run geplant ist)
                        if (data.seconds_until_next_run !== null && data.seconds_until_next_run > 0) {
                            // Countdown anzeigen
                            headerCountdown.style.display = 'flex';
                            
                            const seconds = data.seconds_until_next_run;
                            const hours = Math.floor(seconds / 3600);
                            const minutes = Math.floor((seconds % 3600) / 60);
                            const secs = seconds % 60;
                            
                            const timeStr = hours > 0 
                                ? `${hours}h ${minutes}m`
                                : minutes > 0
                                    ? `${minutes}m ${secs}s`
                                    : `${secs}s`;
                            
                            headerCountdownTime.textContent = timeStr;
                            
                            // Pulse wenn < 1 Minute
                            if (seconds < 60) {
                                headerCountdownTime.classList.add('pulse');
                            } else {
                                headerCountdownTime.classList.remove('pulse');
                            }
                            
                            // Run Now Button anzeigen
                            headerControlBtn.style.display = 'flex';
                            headerControlBtn.classList.remove('pause', 'resume');
                            headerControlBtn.classList.add('run-now');
                            headerControlIcon.textContent = '⏭️';
                            headerControlBtn.title = 'Run Now';
                        } else {
                            // Kein Countdown: Nur Run Now Button
                            headerCountdown.style.display = 'none';
                            headerControlBtn.style.display = 'flex';
                            headerControlBtn.classList.remove('pause', 'resume');
                            headerControlBtn.classList.add('run-now');
                            headerControlIcon.textContent = '⏭️';
                            headerControlBtn.title = 'Run Now';
                        }
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
                            const endTime = new Date(item.end_time);
                            const timeStr = endTime.toLocaleString('de-DE');
                            const duration = item.duration_seconds || 0;
                            const hours = Math.floor(duration / 3600);
                            const minutes = Math.floor((duration % 3600) / 60);
                            const seconds = duration % 60;
                            const durationStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m ${seconds}s`;
                            
                            const markerClass = item.success ? 'success' : 'failed';
                            const borderColor = item.success ? '#10b981' : '#ef4444';
                            
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
                                                <span>📦</span> ${item.archive_count || 0} archives
                                            </div>
                                            <div class="timeline-meta-item">
                                                <span>${item.success ? '✓' : '✗'}</span> ${item.success ? 'Success' : 'Failed'}
                                            </div>
                                        </div>
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
        updateStatus();
        setInterval(updateStatus, 1000); // Updated to 1s for live countdown (v2.1.0)
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
        template = get_html_template()
        return render_template_string(template, version=__version__)

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

    @app.route("/api/theme", methods=["GET", "POST"])
    def api_theme() -> Any:
        """Get or set theme preference."""
        if request.method == "POST":
            data = request.get_json()
            theme = data.get("theme", "dark")
            tracker.set_theme(theme)
            return jsonify({"status": "ok", "theme": theme})
        else:
            return jsonify({"theme": tracker.get_theme()})

    @app.route("/api/control/pause", methods=["POST"])
    def api_pause() -> Any:
        """Pause processing."""
        tracker.pause_processing()
        tracker.add_notification("info", "Processing Paused", "Processing has been paused by user")
        return jsonify({"status": "ok"})

    @app.route("/api/control/resume", methods=["POST"])
    def api_resume() -> Any:
        """Resume processing."""
        tracker.resume_processing()
        tracker.add_notification("info", "Processing Resumed", "Processing has been resumed")
        return jsonify({"status": "ok"})

    @app.route("/api/history")
    def api_history() -> Any:
        """Get processing history."""
        status = tracker.get_status()
        return jsonify(status.to_dict().get("history", []))

    @app.route("/api/health")
    def api_health() -> Any:
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "cineripr-webgui"})

    # NEW API Endpoints for v2.1.0

    @app.route("/api/settings", methods=["GET"])
    def api_settings_get_all() -> Any:
        """Get all settings."""
        db = get_settings_db()
        return jsonify(db.get_all())

    @app.route("/api/settings/<key>", methods=["GET", "POST"])
    def api_settings_item(key: str) -> Any:
        """Get or update a specific setting."""
        db = get_settings_db()

        if request.method == "GET":
            value = db.get(key)
            return jsonify({"key": key, "value": value})

        elif request.method == "POST":
            data = request.get_json()
            if not data or "value" not in data:
                return jsonify({"error": "Missing 'value' in request body"}), 400
            db.set(key, data["value"])
            tracker.add_notification("success", "Setting Updated", f"'{key}' has been updated")
            return jsonify({"status": "saved", "key": key, "value": data["value"]})

        return jsonify({"error": "Method not allowed"}), 405

    @app.route("/api/settings/performance", methods=["GET", "POST"])
    def api_settings_performance() -> Any:
        """Get or update performance settings."""
        db = get_settings_db()

        if request.method == "GET":
            return jsonify({
                "parallel_extractions": db.get("parallel_extractions", 1),
                "cpu_cores_per_extraction": db.get("cpu_cores_per_extraction", 2),
                "auto_detect_hardware": db.get("auto_detect_hardware", True),
                "max_ram_usage_percent": db.get("max_ram_usage_percent", 75),
                "min_free_ram_gb": db.get("min_free_ram_gb", 4.0),
                "ssd_only_parallel": db.get("ssd_only_parallel", True),
            })

        elif request.method == "POST":
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Update performance settings
            for key in [
                "parallel_extractions",
                "cpu_cores_per_extraction",
                "auto_detect_hardware",
                "max_ram_usage_percent",
                "min_free_ram_gb",
                "ssd_only_parallel",
            ]:
                if key in data:
                    db.set(key, data[key])

            tracker.add_notification("success", "Performance Settings Updated", "Settings will apply on next run")
            return jsonify({"status": "saved"})

        return jsonify({"error": "Method not allowed"}), 405

    @app.route("/api/control/trigger-now", methods=["POST"])
    def api_trigger_now() -> Any:
        """Skip sleep and trigger next run immediately."""
        tracker.trigger_run_now()
        tracker.add_notification("info", "Manual Trigger", "Starting next run immediately...")
        return jsonify({"status": "triggered"})

    @app.route("/api/system/hardware", methods=["GET"])
    def api_system_hardware() -> Any:
        """Get hardware information."""
        try:
            import psutil

            # Detect disk type (simplified - returns unknown on Windows)
            disk_type = "unknown"
            try:
                # This would need platform-specific logic
                # For now, we'll just return unknown
                disk_type = "SSD"  # TODO: Implement proper detection
            except Exception:
                pass

            return jsonify({
                "cpu_count": psutil.cpu_count(),
                "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
                "disk_type": disk_type,
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/setup/wizard", methods=["POST"])
    def api_setup_wizard() -> Any:
        """Complete setup wizard."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        profile = data.get("profile", "conservative")
        db = get_settings_db()

        if profile == "power":
            db.set("parallel_extractions", 2)
            db.set("repeat_after_minutes", 15)
            db.set("finished_retention_days", 14)
            db.set("enable_delete", True)
            db.set("include_other", True)
        # conservative profile uses DEFAULT_SETTINGS

        db.mark_initialized()
        tracker.add_notification("success", "Setup Complete", f"Profile '{profile}' has been applied")

        return jsonify({"status": "completed", "profile": profile})

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
