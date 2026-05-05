#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add to boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

# Import the web server
from boxesserver import BServer

def test_spacing_comprehensive():
    """Comprehensive test of spacing parameter handling"""
    
    print("Comprehensive spacing parameter test...")
    
    # Create a mock environ for testing
    class MockEnviron:
        def __init__(self, path_info="/ABox", query_string="x=100&y=100&h=100&spacing=0.5:2&outside=true&render=4"):
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
    
    # Test: Export with spacing values
    print("\nTesting YAML export with spacing values (0.5:2):")
    try:
        environ = MockEnviron(query_string="x=100&y=100&h=100&spacing=0.5:2&outside=true&render=4")
        result = server.serve(environ, mock_start_response)
        
        # Convert result to string and display
        yaml_content = b''.join(result).decode('utf-8')
        print("✓ YAML export successful!")
        print("\nFull YAML Content:")
        print(yaml_content)
        
        # Debug: Check what's in current_params
        box = server.boxes.get('ABox')()
        box.translations = server.getLanguage([], "en-US")
        box.parseArgs(["x=100", "y=100", "h=100", "--spacing", "0.5", "--spacing", "2", "outside=true"])
        
        current_params = box.getOriginalArgs()
        print(f"\nDebug: current_params keys: {sorted(current_params.keys())}")
        print(f"Debug: spacing in current_params: {'spacing' in current_params}")
        if 'spacing' in current_params:
            print(f"Debug: spacing value: {current_params['spacing']}")
            print(f"Debug: spacing type: {type(current_params['spacing'])}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spacing_comprehensive()
