
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from cineripr.extraction.archive_detection import (
    compute_archive_group_key,
    build_archive_groups,
    validate_archive_group,
)

class TestArchiveDetection(unittest.TestCase):
    def test_dctmp_grouping(self):
        """Test that .dctmp files are grouped with their base archive."""
        # Case 1: .rar.dctmp
        p1 = Path("movie.rar.dctmp")
        key1, order1 = compute_archive_group_key(p1)
        self.assertEqual(key1, "movie.rar")
        self.assertEqual(order1, -1)
        
        # Case 2: .r01.dctmp
        p2 = Path("movie.r01.dctmp")
        key2, order2 = compute_archive_group_key(p2)
        # Assuming r01 -> index 1 based on regex
        self.assertEqual(key2, "movie.rar") 
        self.assertEqual(order2, 1)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_validation_blocks_dctmp(self, mock_is_file, mock_exists):
        """Test that validation fails if any member is a .dctmp file."""
        mock_exists.return_value = True
        mock_is_file.return_value = True

        p_main = Path("test.rar")
        p_part = Path("test.r01.dctmp")
        
        # Manually create group as build_archive_groups logic is tested separately
        # and might rely on complex sorting potentially
        # But let's use it to be sure integration works
        groups = build_archive_groups([p_main, p_part])
        self.assertTrue(len(groups) > 0)
        group = groups[0]
        
        is_valid, msg = validate_archive_group(group, check_completeness=False)
        self.assertFalse(is_valid)
        self.assertIsNotNone(msg)
        self.assertIn("still downloading", msg)
        self.assertIn(".dctmp", msg)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_mixed_completeness(self, mock_is_file, mock_exists):
        """Test a mix of complete and incomplete files in the same group."""
        mock_exists.return_value = True
        mock_is_file.return_value = True

        files = [
            Path("archive.part01.rar"),
            Path("archive.part02.rar"),
            Path("archive.part03.rar.dctmp")
        ]
        groups = build_archive_groups(files)
        self.assertEqual(len(groups), 1)
        
        is_valid, msg = validate_archive_group(groups[0], check_completeness=False)
        self.assertFalse(is_valid)
        self.assertIn("archive.part03.rar.dctmp", msg)

if __name__ == '__main__':
    unittest.main()
