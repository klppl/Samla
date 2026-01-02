
import argparse
import requests
import re
import os
from datetime import datetime
from pathlib import Path

def register_commands(subparsers):
    parser = subparsers.add_parser("import-linkding", help="Import bookmarks from Linkding API")
    parser.add_argument("--url", required=True, help="Linkding Instance URL")
    parser.add_argument("--token", required=True, help="API Token")
    parser.add_argument("--tag", default="shared", help="Tag to filter by (default: shared)")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of bookmarks to fetch")
    parser.set_defaults(func=command_import_linkding)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9-]', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

import json

def command_import_linkding(args):
    print(f"Fetching bookmarks from {args.url} (tag: {args.tag})...")
    # ... (rest of function setup) ...
    # headers are handled by cloudscraper
    
    params = {
        "q": f"#{args.tag}",
        "limit": args.limit,
        "format": "json"
    }
    
    # Load Archetype
    archetype_path = Path("archetypes/bookmarks.md")
    if not archetype_path.exists():
        print("Error: archetypes/bookmarks.md not found.")
        return

    with open(archetype_path, 'r', encoding='utf-8') as f:
        archetype_template = f.read()

    import cloudscraper
    scraper = cloudscraper.create_scraper()
    
    headers = {
        "Authorization": f"Token {args.token}"
    }

    try:
        response = scraper.get(f"{args.url.rstrip('/')}/api/bookmarks/", headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error Code: {response.status_code}")
            print(f"Response Body: {response.text}")
            response.raise_for_status()
            
        try:
            data = response.json()
        except Exception as e:
            print(f"Failed to decode JSON. Status: {response.status_code}")
            print(f"Response Content: {response.text}")
            raise e
        
        results = data.get('results', [])
        print(f"Found {len(results)} bookmarks.")
        
        base_dir = Path("content/bookmarks")
        base_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for bookmark in results:
            title = bookmark.get('title') or bookmark.get('website_title') or "Untitled"
            url = bookmark.get('url')
            desc = bookmark.get('description', '')
            
            # Date format: 2023-10-27T10:00:00Z -> 2023-10-27
            date_str = bookmark.get('date_added', '')[:10]
            
            slug = slugify(title)
            
            target_dir = base_dir / slug
            target_file = target_dir / "post.md"
            
            if target_file.exists():
                print(f"Skipping existing: {slug}")
                continue
                
            target_dir.mkdir(exist_ok=True)
            
            # Use JSON dumps for safe string representation (handles quotes, newlines, etc.)
            safe_title = json.dumps(title, ensure_ascii=False)
            safe_url_str = json.dumps(url, ensure_ascii=False)
            safe_desc_str = json.dumps(desc, ensure_ascii=False)
            
            current_content = archetype_template
            
            # Replace placeholders in Archetype using lambda to avoid regex escape issues
            current_content = re.sub(r'title:\s*"{title}"', lambda m: f'title: {safe_title}', current_content) 
            current_content = current_content.replace("{datetime}", date_str) 
            
            # Populate empty fields (link, tags)
            current_content = re.sub(r'^link:\s*$', lambda m: f'link: {safe_url_str}', current_content, flags=re.MULTILINE)
            
            # Force hide_from_home to true
            current_content = re.sub(r'^hide_from_home:\s*false$', 'hide_from_home: true', current_content, flags=re.MULTILINE)
            
            tags_list = bookmark.get('tag_names', [])
            # Remove the sync tag (e.g. 'bloggen') from the tags list
            if args.tag in tags_list:
                tags_list.remove(args.tag)
            current_content = re.sub(r'^tags:\s*\[\]$', lambda m: f'tags: {tags_list}', current_content, flags=re.MULTILINE)

            # Append description to body
            if desc:
                 current_content = current_content.replace("Write your commentary here...", desc)

            with open(target_file, "w", encoding='utf-8') as f:
                f.write(current_content)
            
            print(f"Imported: {slug}")
            count += 1
            
        print(f"Import complete. {count} new bookmarks.")
        
    except Exception as e:
        print(f"Error fetching bookmarks: {e}")
