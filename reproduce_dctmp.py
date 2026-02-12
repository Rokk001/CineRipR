
import unittest
from pathlib import Path
from cineripr.extraction.archive_detection import is_supported_archive, compute_archive_group_key

class TestDctmpGrouping(unittest.TestCase):
    def test_dctmp_handling(self):
        # Test file like "anaconda...r18.dctmp"
        p = Path("anaconda.2025.german.dl.1080p.web.x264-wvf.r18.dctmp")
        
        # 1. Is it supported?
        supported = is_supported_archive(p)
        print(f"Is supported: {supported}")
        
        # 2. How is it grouped?
        key, order = compute_archive_group_key(p)
        print(f"Key: {key}, Order: {order}")
        
        # If it returns (filename, -1), it's treated as a single isolated archive, 
        # which is WRONG for a volume r18.
        
        # Test regular rar for comparison
        p_rar = Path("anaconda.2025.german.dl.1080p.web.x264-wvf.rar")
        key_rar, order_rar = compute_archive_group_key(p_rar)
        print(f"RAR Key: {key_rar}, Order: {order_rar}")

if __name__ == '__main__':
    unittest.main()
