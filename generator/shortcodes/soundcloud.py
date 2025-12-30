import urllib.request
import urllib.parse
import json
import hashlib
import re
from pathlib import Path

# Simple disk cache
CACHE_DIR = Path(".cache/soundcloud")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def render(id_or_url: str, visual: str = "true", title: str = "SoundCloud Player"):
    """
    Renders a responsive SoundCloud embed.
    
    Usage:
    1. With ID: {{< soundcloud 123456789 >}}
    2. With URL: {{< soundcloud "https://soundcloud.com/artist/song" >}}
    
    HOW TO FIND THE ID:
    1. Go to https://w.soundcloud.com/player/?url=<PASTE YOUR SOUNDCLOUD URL HERE>
    2. Look at the transformed URL in the browser address bar.
    3. Copy the number after 'tracks/'. That is your ID (e.g., 716018269).
    """
    
    track_id = id_or_url
    
    # Check if input looks like a URL
    if str(id_or_url).startswith('http'):
        url = id_or_url
        # Check cache
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        cache_file = CACHE_DIR / f"{url_hash}.json"
        
        cached_id = None
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    cached_id = data.get('track_id')
            except:
                pass
                
        if cached_id:
            track_id = cached_id
            try:
                params = urllib.parse.urlencode({'format': 'json', 'url': url})
                oembed_url = f"https://soundcloud.com/oembed?{params}"
                
                req = urllib.request.Request(
                    oembed_url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )

                with urllib.request.urlopen(req) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        html_resp = data.get('html', '')
                        
                        # Extract ID
                        match = re.search(r'tracks/(\d+)', html_resp)
                        if not match:
                            match = re.search(r'tracks%2F(\d+)', html_resp)
                            
                        if match:
                            track_id = match.group(1)
                            # Cache it
                            with open(cache_file, 'w') as f:
                                json.dump({'track_id': track_id}, f)
                        else:
                            print(f"Could not extract Track ID for {url}")
                            # Fallback to display errors or placeholder? 
                            # For now, let it fall through, it will likely fail in iframe
                    else:
                        print(f"Error resolving SoundCloud URL: {response.status}")
            except Exception as e:
                print(f"Exception resolving SoundCloud ID: {e}")

    # Handle string 'true'/'false'
    visual_param = "true" if str(visual).lower() == 'true' else "false"
    
    html = f"""
<div style="width: 100%; height: 166px; margin-bottom: 1.5rem; overflow: hidden; border-radius: 8px;">
    <iframe width="100%" height="166" scrolling="no" frameborder="no" allow="autoplay" 
        src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/{track_id}&color=%23ff5500&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true&visual={visual_param}"
        title="{title}">
    </iframe>
</div>
"""
    return html
