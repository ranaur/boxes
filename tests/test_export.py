#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

from boxes_cli import main

def test_export():
    """Test the --export functionality"""
    
    print("Testing --export functionality...")
    
    # Test 1: Export with default parameters
    print("\n1. Testing export with defaults:")
    try:
        # Simulate sys.argv for CLI call
        original_argv = sys.argv
        sys.argv = ["boxes_cli", "build", "ABox", "--export", "test_defaults.yaml"]
        main()
        sys.argv = original_argv
        print("   ✓ Export with defaults completed")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Export with custom parameters
    print("\n2. Testing export with custom parameters:")
    try:
        # Simulate sys.argv for CLI call
        original_argv = sys.argv
        sys.argv = ["boxes_cli", "build", "ABox", "--thickness", "5.0", "--burn", "0.2", "--debug", "true", "--export", "test_custom.yaml"]
        main()
        sys.argv = original_argv
        print("   ✓ Export with custom parameters completed")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Check if files were created
    print("\n3. Checking generated files:")
    for filename in ["test_defaults.yaml", "test_custom.yaml"]:
        if os.path.exists(filename):
            print(f"   ✓ {filename} created")
            with open(filename, 'r') as f:
                content = f.read()
                print(f"   Content preview (first 10 lines):")
                for i, line in enumerate(content.split('\n')[:10]):
                    print(f"     {i+1}: {line}")
                if len(content.split('\n')) > 10:
                    print(f"     ... ({len(content.split('\n')) - 10} more lines)")
        else:
            print(f"   ✗ {filename} not found")

if __name__ == "__main__":
    test_export()
