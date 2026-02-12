import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from cineripr.extraction.archive_extraction import test_archive_integrity

class TestArchiveIntegrity(unittest.TestCase):
    @patch("cineripr.extraction.archive_extraction.resolve_seven_zip_command")
    @patch("subprocess.run")
    def test_integrity_success(self, mock_run, mock_resolve):
        mock_resolve.return_value = "7z"
        mock_run.return_value = MagicMock(returncode=0, stdout="Everything is Ok", stderr="")
        
        is_ok, msg = test_archive_integrity(Path("test.rar"), seven_zip_path=Path("7z.exe"))
        self.assertTrue(is_ok)
        self.assertIsNone(msg)

    @patch("cineripr.extraction.archive_extraction.resolve_seven_zip_command")
    @patch("subprocess.run")
    def test_integrity_crc_error(self, mock_run, mock_resolve):
        mock_resolve.return_value = "7z"
        mock_run.return_value = MagicMock(returncode=2, stdout="ERROR: CRC Failed : file.txt", stderr="")
        
        is_ok, msg = test_archive_integrity(Path("bad.rar"), seven_zip_path=Path("7z.exe"))
        self.assertFalse(is_ok)
        self.assertIn("CRC Failed", msg)
        self.assertIn("file.txt", msg)

    @patch("cineripr.extraction.archive_extraction.resolve_seven_zip_command")
    @patch("subprocess.run")
    def test_integrity_missing_volume(self, mock_run, mock_resolve):
        mock_resolve.return_value = "7z"
        mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="Missing volume : part2.rar")
        
        is_ok, msg = test_archive_integrity(Path("incomplete.rar"), seven_zip_path=Path("7z.exe"))
        self.assertFalse(is_ok)
        self.assertIn("Missing volume", msg)

    @patch("cineripr.extraction.archive_extraction.resolve_seven_zip_command")
    def test_no_7zip(self, mock_resolve):
        mock_resolve.return_value = None
        is_ok, msg = test_archive_integrity(Path("test.rar"), seven_zip_path=None)
        self.assertFalse(is_ok)
        self.assertIn("not found", msg)
