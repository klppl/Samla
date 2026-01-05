import yaml
from pathlib import Path
from typing import Any
from .models import SiteConfig, MenuLink

def load_config(config_path: str) -> SiteConfig:
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    site = data.get('site', {})
    content = data.get('content', {})
    features = data.get('features', {})
    social = data.get('social', {})
    style = data.get('style', {})
    humans = data.get('humans', {})
    menu_data = data.get('menu', [])
    
    menu = []
    
    if isinstance(menu_data, dict):
        # Handle rows (first_row, second_row, etc.)
        # We assume iteration order is preserved (Python 3.7+)
        is_first_row = True
        for row_name, items in menu_data.items():
            if not isinstance(items, list): continue
            
            for i, item in enumerate(items):
                # Force break_before on the first item of subsequent rows
                force_break = (not is_first_row) and (i == 0)
                
                menu.append(MenuLink(
                    name=item['name'], 
                    url=item['url'], 
                    icon=item.get('icon', ''), 
                    type=item.get('type'),
                    break_before=item.get('break_before', False) or force_break
                ))
            is_first_row = False
            
    elif isinstance(menu_data, list):
        # Handle legacy flat list
        menu = [MenuLink(
            name=item['name'], 
            url=item['url'], 
            icon=item.get('icon', ''), 
            type=item.get('type'),
            break_before=item.get('break_before', False)
        ) for item in menu_data]
    
    frontpage_filter = data.get('frontpage_filter', {})
    index_filter = data.get('index_filter', {})

    return SiteConfig(
        title=site.get('title', 'My Site'),
        subtitle=site.get('subtitle', ''),
        base_url=site.get('base_url', ''),
        timezone=site.get('timezone', 'UTC'),
        language=site.get('language', 'en'),
        menu=menu,
        content_dir=content.get('input_dir', 'content'),
        output_dir=content.get('output_dir', 'public'),
        posts_per_page=content.get('posts_per_page', 10),
        features=features,
        social=social,
        style=style,
        humans=humans,
        background_image=site.get('background_image', ''),
        frontpage_filter=frontpage_filter,
        index_filter=index_filter
    )
