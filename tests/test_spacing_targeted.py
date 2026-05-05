#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add to boxes scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'boxes' / 'scripts'))

# Import the web server
from boxesserver import BServer

def test_spacing_targeted():
    """Targeted test of spacing parameter in YAML export"""
    
    print("Targeted test of spacing parameter in YAML export...")
    
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
        
        # Debug: Check YAML export logic step by step
        print("\nDebugging YAML export logic:")
        
        # Replicate the YAML export logic
        default_params = box.getDefaultArgs()
        yaml_lines = []
        yaml_lines.append(f"# Exported current parameters for {current_params.get('box_type', 'Unknown')}")
        yaml_lines.append(f"# Values same as defaults are commented")
        yaml_lines.append("")
        yaml_lines.append("box_type: " + current_params.get("box_type", "Unknown"))
        yaml_lines.append("name: \"" + current_params.get("name", "example") + "\"")
        yaml_lines.append("generate: " + current_params.get("generate", "true"))
        yaml_lines.append("args:")
        
        # Sort parameters for consistent output
        for key in sorted(current_params.keys()):
            if key in ["box_type", "name", "generate"]:
                continue  # Already handled above
                
            current_value = current_params[key]
            default_value = default_params.get(key, None)
            
            print(f"Debug: Processing key '{key}': current='{current_value}', default='{default_value}'")
            
            # For dimension parameters when outside=true, use original user input values
            if key in ['x', 'y', 'h', 'spacing'] and box.original_args.get('outside', False):
                # Use the original user input value
                original_value = box.original_args.get(key, current_value)
                # Handle tuple values properly (like spacing parameter)
                if isinstance(original_value, tuple):
                    original_value = str(original_value[0]) if original_value else str(original_value)
                else:
                    original_value = str(original_value)
                # Compare against the actual argparser default
                if original_value == default_value:
                    yaml_lines.append(f"  # {key}: {original_value}")
                else:
                    yaml_lines.append(f"  {key}: {original_value}")
                print(f"Debug: -> Using original_value: {original_value}")
            else:
                # Comment if value is same as default
                if current_value == default_value:
                    yaml_lines.append(f"  # {key}: {current_value}")
                else:
                    yaml_lines.append(f"  {key}: {current_value}")
                print(f"Debug: -> Using current_value: {current_value}")
        
        # Check final YAML content
        yaml_content = '\n'.join(yaml_lines)
        print(f"\nFinal YAML content (first 50 lines):")
        lines = yaml_content.split('\n')
        for i, line in enumerate(lines[:50]):
            print(f"  {i+1:2d}: {line}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spacing_targeted()
