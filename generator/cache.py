import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class CacheManager:
    def __init__(self, cache_dir: str = '.cache', cache_file: str = 'markdown_cache.json'):
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / cache_file
        self.cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def get(self, file_path: str, mtime: float) -> Optional[Dict[str, Any]]:
        """
        Get cached data if valid.
        
        Args:
            file_path: Absolute path or relative path key.
            mtime: Current modification time of the file.
            
        Returns:
            Dict containing 'html', 'frontmatter' if valid, else None.
        """
        key = str(file_path)
        if key in self.cache:
            entry = self.cache[key]
            # Check if cache is fresh
            if entry.get('mtime') == mtime:
                return entry['data']
        return None

    def set(self, file_path: str, mtime: float, data: Dict[str, Any]):
        """Update cache entry."""
        key = str(file_path)
        self.cache[key] = {
            'mtime': mtime,
            'data': data
        }

    def save(self):
        """Persist cache to disk."""
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
