# Debug script to examine the argparser structure
import sys
import os

# Add the boxes directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boxes'))

from boxes.generators.abox import ABox

def debug_parser():
    """Debug the argparser structure"""
    
    # Create an ABox instance
    box = ABox()
    
    print("=== Argument Parser Structure ===")
    print(f"Number of action groups: {len(box.argparser._action_groups)}")
    
    for i, group in enumerate(box.argparser._action_groups):
        print(f"\nGroup {i}: {group.title}")
        if hasattr(group, 'prefix'):
            print(f"  Prefix: {group.prefix}")
        else:
            print(f"  Prefix: None")
        
        print(f"  Number of actions: {len(group._actions)}")
        
        for j, action in enumerate(group._actions):
            if hasattr(action, 'dest') and action.dest != 'help':
                print(f"    Action {j}: {action.dest} = {action.default}")
    
    print("\n=== Testing getDefaultArgs Method ===")
    if hasattr(box, 'getDefaultArgs'):
        defaults = box.getDefaultArgs()
        print(f"Method returned {len(defaults)} arguments:")
        
        for key in sorted(defaults.keys()):
            print(f"  {key} = {defaults[key]}")
    else:
        print("Method not found!")

if __name__ == "__main__":
    debug_parser()
