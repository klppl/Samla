
import argparse
import requests
import re
import os
import json
from datetime import datetime
from pathlib import Path
import cloudscraper

def register_commands(subparsers):
    parser = subparsers.add_parser("import-readeck", help="Import articles from Readeck API")
    parser.add_argument("--url", required=True, help="Readeck Instance URL")
    parser.add_argument("--token", required=True, help="API Token")
    parser.add_argument("--limit", type=int, default=100, help="Limit number of articles to fetch")
    parser.set_defaults(func=command_import_readeck)

def command_import_readeck(args):
    print(f"Fetching articles from {args.url}...")
    
    # data/readeck.json
    data_file = Path("data/readeck.json")
    existing_data = []
    if data_file.exists():
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read existing data: {e}")

    # Index existing by URL to avoid duplicates/overwrite
    data_map = {item['url']: item for item in existing_data}

    # Clean URL
    base_url = args.url.rstrip('/')
    api_url = f"{base_url}/api/bookmarks" 
    
    params = {
        "limit": args.limit,
        "archived": "false"
    }
    
    headers = {
        "Authorization": f"Bearer {args.token}",
        "Accept": "application/json"
    }

    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(api_url, headers=headers, params=params)
        
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
        
        if isinstance(data, list):
            results = data
        else:
            results = data.get('results', []) or data.get('data', [])

        print(f"Found {len(results)} articles.")
        
        count = 0
        for item in results:
            url = item.get('url')
            if not url: continue

            title = item.get('title') or "Untitled"
            desc = item.get('excerpt', '') or item.get('description', '')
            
            # Date handling
            # Field is 'created' based on debug output
            date_str = item.get('created', '')
            # Ensure we have a valid ISOish string
            if not date_str:
                date_str = datetime.now().isoformat()
            
            # Standardize date to YYYY-MM-DD for grouping
            display_date = date_str[:10]
            
            new_entry = {
                "title": title,
                "url": url,
                "description": desc,
                "date": display_date,
                "tags": item.get('labels', []) # debug showed 'labels'
            }
            
            # Update or Add
            if url not in data_map:
                count += 1
            
            data_map[url] = new_entry
            
        # Convert back to list and sort
        final_list = list(data_map.values())
        final_list.sort(key=lambda x: x['date'], reverse=True)
        
        # Ensure data dir exists
        data_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(final_list, f, indent=2, ensure_ascii=False)
            
        print(f"Import complete. {count} new/updated articles saved to {data_file}.")
        
    except Exception as e:
        print(f"Error fetching articles: {e}")
