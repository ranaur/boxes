import sys
import os
from pathlib import Path

# Add the boxes directory to the path
sys.path.append(Path(__file__).resolve().parent.__str__())

import boxes.generators

def debug_generators():
    """Debug the generator loading"""
    
    print("=== Debugging Generators ===")
    
    # Get all generators
    all_generators = boxes.generators.getAllBoxGenerators()
    
    print(f"Total generators found: {len(all_generators)}")
    print("Available generators:")
    
    for name in sorted(all_generators.keys()):
        print(f"  - {name}")
    
    # Check specifically for ABox
    if 'ABox' in all_generators:
        print("\n✓ ABox found!")
        abox_class = all_generators['ABox']
        print(f"ABox class: {abox_class}")
        
        # Try to create an instance
        try:
            abox = abox_class()
            print("✓ ABox instance created successfully")
            
            # Check if method exists
            if hasattr(abox, 'getDefaultArgs'):
                print("✓ getDefaultArgs method found")
                
                # Try to call it
                defaults = abox.getDefaultArgs()
                print(f"✓ getDefaultArgs returned {len(defaults)} arguments")
                
                # Show first few arguments
                print("First 10 arguments:")
                for i, (key, value) in enumerate(sorted(defaults.items())):
                    if i >= 10:
                        break
                    print(f"  {key} = {value}")
            else:
                print("✗ getDefaultArgs method not found")
                
        except Exception as e:
            print(f"✗ Error creating ABox instance: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n✗ ABox not found!")

if __name__ == "__main__":
    debug_generators()
