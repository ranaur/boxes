import sys
import os
from pathlib import Path

# Add the boxes directory to the path
sys.path.append(Path(__file__).resolve().parent.__str__())

import boxes.generators

def debug_abox_args():
    """Debug ABox arguments"""
    
    # Get ABox generator
    all_generators = boxes.generators.getAllBoxGenerators()
    abox_class = all_generators.get('boxes.generators.abox.ABox')
    
    if abox_class is None:
        print("ABox not found!")
        return
    
    abox = abox_class()
    defaults = abox.getDefaultArgs()
    
    print("=== ABox Default Arguments ===")
    print(f"Total arguments: {len(defaults)}")
    
    print("\nAll arguments:")
    for key in sorted(defaults.keys()):
        print(f"  {key} = {defaults[key]}")
    
    print("\n=== FingerJoint related arguments ===")
    fingerjoint_args = [key for key in defaults.keys() if 'FingerJoint' in key]
    for key in sorted(fingerjoint_args):
        print(f"  {key} = {defaults[key]}")
    
    print("\n=== Lid related arguments ===")
    lid_args = [key for key in defaults.keys() if 'Lid' in key]
    for key in sorted(lid_args):
        print(f"  {key} = {defaults[key]}")

if __name__ == "__main__":
    debug_abox_args()
