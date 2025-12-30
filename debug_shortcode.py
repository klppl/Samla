import sys
import os

# Ensure we can import generator modules
sys.path.append(os.getcwd())

from generator.shortcode_manager import ShortcodeManager

try:
    mgr = ShortcodeManager()
    print(f"Loaded shortcodes: {list(mgr.shortcodes.keys())}")
    
    content = '{{< email "test@test.com" >}}'
    result = mgr.process(content)
    
    print(f"Input: {content}")
    print(f"Output: {result}")
    
    if "String.fromCharCode" in result:
        print("SUCCESS: Shortcode rendered.")
    elif result == content:
        print("FAILURE: Shortcode returned raw content.")
    else:
        print("FAILURE: Unknown output.")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
