"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests.
    
    Args:
        tmp_path: pytest's temporary directory fixture
        
    Returns:
        Path to temporary directory
    """
    return tmp_path


@pytest.fixture
def downloads_dir(temp_dir: Path) -> Path:
    """Create a downloads directory.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path to downloads directory
    """
    downloads = temp_dir / "downloads"
    downloads.mkdir()
    return downloads


@pytest.fixture
def extracted_dir(temp_dir: Path) -> Path:
    """Create an extracted directory.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path to extracted directory
    """
    extracted = temp_dir / "extracted"
    extracted.mkdir()
    return extracted


@pytest.fixture
def finished_dir(temp_dir: Path) -> Path:
    """Create a finished directory.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path to finished directory
    """
    finished = temp_dir / "finished"
    finished.mkdir()
    return finished

