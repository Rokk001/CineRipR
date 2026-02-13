
import binascii
import sys

try:
    with open('src/cineripr/web/settings_db.py', 'rb') as f:
        content = f.read()
        
    lines = content.splitlines(keepends=True)
    
    target_indices = [455, 458, 469, 473] # 0-indexed
    for target_idx in target_indices:
        if target_idx < len(lines):
            line = lines[target_idx]
            print(f"Line {target_idx+1} length: {len(line)}")
            print(f"Hex: {binascii.hexlify(line)}")
            print(f"Repr: {repr(line)}")
        else:
            print(f"Line {target_idx+1} does not exist. Total lines: {len(lines)}")

except Exception as e:
    print(f"Error: {e}")
