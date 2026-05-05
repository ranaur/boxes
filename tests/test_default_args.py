#!/usr/bin/env python3

import sys
import os

# Add the boxes directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boxes'))

from boxes.generators.abox import ABox

def test_get_default_args():
    """Test the getDefaultArgs method"""
    
    # Create an ABox instance
    box = ABox()
    
    # Get the default arguments
    defaults = box.getDefaultArgs()
    
    print("Default arguments for ABox:")
    print("=" * 50)
    
    # Sort the keys for consistent output
    for key in sorted(defaults.keys()):
        print(f"{key} = {defaults[key]}")
    
    print(f"\nTotal arguments: {len(defaults)}")
    
    # Check for expected keys
    expected_keys = ["box_type", "name", "generate", "thickness", "burn", "format"]
    for key in expected_keys:
        if key in defaults:
            print(f"✓ Found expected key: {key}")
        else:
            print(f"✗ Missing expected key: {key}")

if __name__ == "__main__":
    test_get_default_args()
