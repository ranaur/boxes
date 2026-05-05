# Simple verification script to check if getDefaultArgs method exists and works
import sys
import os

# Add the boxes directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boxes'))

try:
    from boxes.generators.abox import ABox
    
    # Create an ABox instance
    box = ABox()
    
    # Check if the method exists
    if hasattr(box, 'getDefaultArgs'):
        print("✓ getDefaultArgs method exists")
        
        # Try to call it
        try:
            defaults = box.getDefaultArgs()
            print(f"✓ Method executed successfully, returned {len(defaults)} arguments")
            
            # Show some sample arguments
            sample_keys = ['box_type', 'name', 'generate', 'thickness', 'burn']
            for key in sample_keys:
                if key in defaults:
                    print(f"  {key} = {defaults[key]}")
                else:
                    print(f"  {key} = (not found)")
                    
        except Exception as e:
            print(f"✗ Error calling method: {e}")
    else:
        print("✗ getDefaultArgs method not found")
        
except ImportError as e:
    print(f"✗ Import error: {e}")

print("Verification complete.")
