#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

# Import the main function directly
from boxes_cli import cmd_build, ArgumentParserError

def test_export():
    """Test the export functionality directly"""
    
    print("Testing --export functionality directly...")
    
    # Test 1: Export with defaults
    print("\n1. Testing export with defaults:")
    try:
        # Create a mock args object
        class MockArgs:
            def __init__(self):
                self.export = "test_defaults.yaml"
                self.file_or_generator = "ABox"
                self.generator_args = []
                self.parameters = None
                self.verbose = False
                self.debug = False
                
        args = MockArgs()
        cmd_build(args)
        print("   ✓ Export with defaults completed")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Export with custom parameters
    print("\n2. Testing export with custom parameters:")
    try:
        # Create a mock args object
        class MockArgs:
            def __init__(self):
                self.export = "test_custom.yaml"
                self.file_or_generator = "ABox"
                self.generator_args = ["--thickness", "5.0", "--burn", "0.2", "--debug", "true"]
                self.parameters = None
                self.verbose = False
                self.debug = False
                
        args = MockArgs()
        cmd_build(args)
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
                print(f"   Content preview (first 15 lines):")
                for i, line in enumerate(content.split('\n')[:15]):
                    print(f"     {i+1}: {line}")
                if len(content.split('\n')) > 15:
                    print(f"     ... ({len(content.split('\n')) - 15} more lines)")
        else:
            print(f"   ✗ {filename} not found")

if __name__ == "__main__":
    test_export()
