
import binascii

try:
    with open('src/cineripr/web/settings_db.py', 'rb') as f:
        # lines are 0-indexed, so line 495 is index 494
        lines = f.readlines()
        content = lines[494]
        print(f"Line 495 (repr): {repr(content)}")
        print(f"Line 495 (hex): {binascii.hexlify(content)}")
        
        # Check surrounding lines too
        print(f"Line 494 (repr): {repr(lines[493])}")
        print(f"Line 496 (repr): {repr(lines[495])}")

except Exception as e:
    print(f"Error: {e}")
