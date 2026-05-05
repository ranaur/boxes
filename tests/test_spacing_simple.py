#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add to boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

# Import the web server
from boxesserver import BServer

def test_spacing_simple():
    """Test spacing parameter with simple format"""
    
    print("Testing spacing parameter with simple format...")
    
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
    
    # Test: Export with simple spacing format
    print("\nTesting YAML export with simple spacing format (0.5:2):")
    try:
        environ = MockEnviron(query_string="x=100&y=100&h=100&spacing=0.5:2&outside=true&render=4")
        result = server.serve(environ, mock_start_response)
        
        # Convert result to string and display
        yaml_content = b''.join(result).decode('utf-8')
        print("✓ YAML export successful!")
        print("\nYAML Content (showing spacing parameter):")
        lines = yaml_content.split('\n')
        for i, line in enumerate(lines):
            if 'spacing:' in line:
                print(f"  {i+1:2d}: {line}")
                
        # Check if spacing is correct
        yaml_dict = {}
        for line in lines:
            if ':' in line and not line.strip().startswith('#'):
                key, value = line.split(':', 1)
                yaml_dict[key.strip()] = value.strip()
        
        print(f"\nSpacing value in YAML:")
        print(f"  spacing: {yaml_dict.get('spacing', 'not found')}")
        
        # Verify fix
        if yaml_dict.get('spacing') == '(0.5, 2.0)':
            print("\n✅ SUCCESS: Spacing is correctly showing multiple values (0.5, 2.0)")
        else:
            print(f"\n❌ FAILURE: Spacing is showing wrong value: {yaml_dict.get('spacing', 'not found')}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spacing_simple()
