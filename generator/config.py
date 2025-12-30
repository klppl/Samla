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
    humans = data.get('humans', {})
    menu_data = data.get('menu', [])
    
    menu = [MenuLink(
        name=item['name'], 
        url=item['url'], 
        icon=item.get('icon', ''), 
        type=item.get('type'),
        break_before=item.get('break_before', False)
    ) for item in menu_data]
    
    frontpage_filter = data.get('frontpage_filter', {})

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
        humans=humans,
        background_image=site.get('background_image', ''),
        frontpage_filter=frontpage_filter
    )
