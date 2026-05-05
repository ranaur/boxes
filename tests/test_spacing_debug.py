#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add to boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

# Import the web server
from boxesserver import BServer

def test_spacing_debug():
    """Debug spacing parameter issue"""
    
    print("Debugging spacing parameter...")
    
    # Create a mock environ for testing
    class MockEnviron:
        def __init__(self, path_info="/ABox", query_string="x=100&y=100&h=100&spacing=0.5:2:3&outside=true&render=4"):
            self.data = {
                "PATH_INFO": path_info,
                "QUERY_STRING": query_string,
                "HTTP_HOST": "localhost:8000",
                "wsgi.url_scheme": "http",
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "8000",
                "SCRIPT_NAME": "",
                "wsgi.file_wrapper": lambda f, size: f
            }
        
        def __getitem__(self, key):
            return self.data[key]
        
        def get(self, key, default=None):
            return self.data.get(key, default)
    
    # Create a mock start_response
    def mock_start_response(status, headers):
        print(f"Status: {status}")
        print("Headers:")
        for header in headers:
            print(f"  {header[0]}: {header[1]}")
        print()
    
    # Create server instance
    server = BServer()
    
    # Test: Export with multiple spacing values
    print("\nTesting YAML export with multiple spacing values (0.5:2:3):")
    try:
        environ = MockEnviron(query_string="x=100&y=100&h=100&spacing=0.5:2:3&outside=true&render=4")
        result = server.serve(environ, mock_start_response)
        
        # Convert result to string and display
        yaml_content = b''.join(result).decode('utf-8')
        print("✓ YAML export successful!")
        print("\nFull YAML Content:")
        print(yaml_content)
        
        # Check what's in the YAML
        print("\nSearching for 'spacing' in YAML:")
        lines = yaml_content.split('\n')
        for i, line in enumerate(lines):
            if 'spacing' in line.lower():
                print(f"  Line {i+1}: {line}")
        
        # Also check what's in current_params
        print("\nDebugging current_params:")
        box = server.boxes.get('ABox')()
        box.translations = server.getLanguage([], "en-US")
        box.parseArgs(["x=100", "y=100", "h=100", "spacing=0.5:2:3", "outside=true"])
        
        current_params = box.getOriginalArgs()
        print(f"  spacing in current_params: {current_params.get('spacing', 'NOT FOUND')}")
        print(f"  original_args spacing: {box.original_args.get('spacing', 'NOT FOUND')}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spacing_debug()
