import re
import shlex
import importlib
import os
import pkgutil
from pathlib import Path
from typing import Dict, Callable, Any

class ShortcodeManager:
    def __init__(self, shortcode_dir: str = 'generator/shortcodes'):
        self.shortcode_dir = Path(shortcode_dir)
        self.shortcodes: Dict[str, Callable] = {}
        self._discover_shortcodes()
        
        # Regex for {{< name args >}} or block {{< name args >}}...{{< /name >}}
        # 1. Name
        # 2. Args
        # 3. Content (optional, if closing tag exists)
        self.pattern = re.compile(r'{{<\s*(\w+)\s*(.*?)\s*>}}(?:(.*?){{<\s*/\1\s*>}})?', re.DOTALL)

    def _discover_shortcodes(self):
        """Dynamically load shortcode modules."""
        # Ensure __init__.py exists
        init_file = self.shortcode_dir / '__init__.py'
        if not init_file.exists():
            with open(init_file, 'w') as f:
                pass

        # Adjust path for importlib
        # We assume generator.shortcodes is the package
        package = 'generator.shortcodes'
        
        for _, name, _ in pkgutil.iter_modules([str(self.shortcode_dir)]):
            try:
                module = importlib.import_module(f'{package}.{name}')
                if hasattr(module, 'render'):
                    self.shortcodes[name] = module.render
                    print(f"Loaded shortcode: {name}")
            except Exception as e:
                print(f"Failed to load shortcode {name}: {e}")

    def process(self, content: str) -> str:
        """Replace shortcodes in content."""
        if not content:
            return content
            
        return self.pattern.sub(self._replace_match, content)

    def _replace_match(self, match) -> str:
        name = match.group(1)
        args_str = match.group(2)
        inner_content = match.group(3) # Can be None
        
        if name not in self.shortcodes:
            print(f"Warning: Shortcode '{name}' not found.")
            return match.group(0) # Return original text
            
        args, kwargs = self._parse_args(args_str)
        
        # Pass inner content if it exists
        if inner_content is not None:
            # Recursively process shortcodes within the block
            inner_content = self.process(inner_content)
            kwargs['content'] = inner_content
        
        try:
            return str(self.shortcodes[name](*args, **kwargs))
        except Exception as e:
            print(f"Error rendering shortcode '{name}': {e}")
            return f"<!-- Error rendering {name}: {e} -->"

    def _parse_args(self, args_str: str):
        """
        Parse arguments string into *args and **kwargs using shlex.
        """
        args = []
        kwargs = {}
        
        try:
            tokens = shlex.split(args_str)
        except ValueError as e:
            print(f"Error parsing shortcode args: {e}")
            return args, kwargs

        for token in tokens:
            if '=' in token:
                # Potential keyword argument
                # But careful: "foo=bar" is key=val, but "url=http://..." is also key=val
                # shlex keeps quoted strings together. 
                # If the token starts with something=, we treat it as kwarg.
                # However, shlex.split("key='val'") results in ["key=val"] (quotes removed by shell logic if they surround value)
                
                parts = token.split('=', 1)
                key = parts[0]
                val = parts[1]
                kwargs[key] = val
            else:
                args.append(token)
                
        return args, kwargs
