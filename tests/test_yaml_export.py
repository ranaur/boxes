#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

# Import the web server
from boxesserver import BServer

def test_yaml_export():
    """Test the YAML export functionality"""
    
    print("Testing YAML export functionality...")
    
    # Create a mock environ for testing
    class MockEnviron:
        def __init__(self, path_info="/ABox", query_string="thickness=5.0&burn=0.2&render=4"):
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
    
    # Test 1: Export with custom parameters
    print("\n1. Testing YAML export with custom parameters:")
    try:
        environ = MockEnviron(query_string="thickness=5.0&burn=0.2&debug=true&render=4")
        result = server.serve(environ, mock_start_response)
        
        # Convert result to string and display
        yaml_content = b''.join(result).decode('utf-8')
        print("✓ YAML export successful!")
        print("\nYAML Content (first 20 lines):")
        lines = yaml_content.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f"  {i+1:2d}: {line}")
        if len(lines) > 20:
            print(f"  ... ({len(lines) - 20} more lines)")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Export with default parameters
    print("\n2. Testing YAML export with defaults:")
    try:
        environ = MockEnviron(query_string="render=4")
        result = server.serve(environ, mock_start_response)
        
        # Convert result to string and display
        yaml_content = b''.join(result).decode('utf-8')
        print("✓ YAML export with defaults successful!")
        print("\nYAML Content (first 20 lines):")
        lines = yaml_content.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f"  {i+1:2d}: {line}")
        if len(lines) > 20:
            print(f"  ... ({len(lines) - 20} more lines)")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yaml_export()
