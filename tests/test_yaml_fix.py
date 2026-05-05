#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

# Import the web server
from boxesserver import BServer

def test_yaml_fix():
    """Test the YAML export fix for outside dimensions"""
    
    print("Testing YAML export fix for outside dimensions...")
    
    # Create a mock environ for testing
    class MockEnviron:
        def __init__(self, path_info="/ABox", query_string="x=100&y=100&h=100&outside=true&render=4"):
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
    
    # Test: Export with outside=true and custom dimensions
    print("\nTesting YAML export with outside=true and custom dimensions (x=100, y=100, h=100):")
    try:
        environ = MockEnviron(query_string="x=100&y=100&h=100&outside=true&render=4")
        result = server.serve(environ, mock_start_response)
        
        # Convert result to string and display
        yaml_content = b''.join(result).decode('utf-8')
        print("✓ YAML export successful!")
        print("\nYAML Content (showing dimension parameters):")
        lines = yaml_content.split('\n')
        for i, line in enumerate(lines):
            if any(param in line for param in ['x:', 'y:', 'h:', 'outside:']):
                print(f"  {i+1:2d}: {line}")
                
        # Check if dimensions are correct (should be 100, not calculated internal values)
        yaml_dict = {}
        for line in lines:
            if ':' in line and not line.strip().startswith('#'):
                key, value = line.split(':', 1)
                yaml_dict[key.strip()] = value.strip()
        
        print(f"\nDimension values in YAML:")
        print(f"  x: {yaml_dict.get('x', 'not found')}")
        print(f"  y: {yaml_dict.get('y', 'not found')}")
        print(f"  h: {yaml_dict.get('h', 'not found')}")
        print(f"  outside: {yaml_dict.get('outside', 'not found')}")
        
        # Verify the fix
        if yaml_dict.get('x') == '100.0' and yaml_dict.get('y') == '100.0' and yaml_dict.get('h') == '100.0':
            print("\n✅ SUCCESS: Dimensions are correctly showing user input values (100.0)")
        else:
            print("\n❌ FAILURE: Dimensions are still showing calculated internal values")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yaml_fix()
