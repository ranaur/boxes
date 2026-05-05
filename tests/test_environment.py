#!/usr/bin/env python3

import sys
import os
import platform
from datetime import datetime

def test_python_environment():
    """Test basic Python environment functionality"""
    
    print("=== Python Environment Test ===")
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Script Location: {os.path.abspath(__file__)}")
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test basic operations
    print("\n=== Basic Operations Test ===")
    
    # Test math operations
    result = 2 + 3 * 4
    print(f"Math test (2 + 3 * 4): {result}")
    
    # Test string operations
    greeting = "Hello"
    name = "Python"
    message = f"{greeting}, {name}!"
    print(f"String test: {message}")
    
    # Test list operations
    numbers = [1, 2, 3, 4, 5]
    doubled = [x * 2 for x in numbers]
    print(f"List test: {numbers} -> {doubled}")
    
    # Test exception handling
    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        print(f"Exception handling test: {type(e).__name__} caught successfully")
    
    # Test imports
    try:
        import json
        import math
        import random
        print("Standard library imports: SUCCESS")
    except ImportError as e:
        print(f"Import error: {e}")
    
    print("\n=== Environment Test Complete ===")
    print("✅ Python environment is working correctly!")

if __name__ == "__main__":
    test_python_environment()
