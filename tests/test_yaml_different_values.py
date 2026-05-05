#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add the boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

# Import the web server
from boxesserver import BServer

def test_yaml_different_values():
    """Test the YAML export with different dimension values"""
    
    print("Testing YAML export with different dimension values...")
    
    # Create a mock environ for testing
    class MockEnviron:
        def __init__(self, path_info="/ABox", query_string="x=150&y=200&h=75&outside=true&render=4"):
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
    
    # Test: Export with outside=true and different dimensions
    print("\nTesting YAML export with outside=true and different dimensions (x=150, y=200, h=75):")
    try:
        environ = MockEnviron(query_string="x=150&y=200&h=75&outside=true&render=4")
        result = server.serve(environ, mock_start_response)
        
        # Convert result to string and display
        yaml_content = b''.join(result).decode('utf-8')
        print("✓ YAML export successful!")
        print("\nYAML Content (showing all lines):")
        lines = yaml_content.split('\n')
        for i, line in enumerate(lines):
            print(f"  {i+1:2d}: {line}")
                
        # Check if dimensions are correct
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
        
        # Also check commented values
        print(f"\nCommented dimension values:")
        for line in lines:
            if any(f"  # {param}:" in line for param in ['x', 'y', 'h']):
                print(f"  {line.strip()}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yaml_different_values()
