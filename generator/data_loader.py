import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any

class DataLoader:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_data(self) -> Dict[str, Any]:
        """
        Scans data directory and loads JSON/YAML files.
        Returns a dictionary where keys are filenames (without extension) 
        and values are parsed content.
        """
        data = {}
        
        if not self.data_dir.exists():
            return data

        for item in self.data_dir.iterdir():
            if item.is_file():
                key = item.stem
                content = None
                
                try:
                    if item.suffix in ['.yaml', '.yml']:
                        with open(item, 'r', encoding='utf-8') as f:
                            content = yaml.safe_load(f)
                    elif item.suffix == '.json':
                        with open(item, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                    
                    if content is not None:
                        data[key] = content
                        print(f"Loaded data file: {item.name}")
                        
                except Exception as e:
                    print(f"Error loading data file {item}: {e}")
                    
        return data
