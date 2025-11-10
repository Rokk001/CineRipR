"""Status tracker service wrapper."""

from ..status import get_status_tracker as _get_status_tracker

def get_status_tracker():
    """Get the global status tracker instance."""
    return _get_status_tracker()

