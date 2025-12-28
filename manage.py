#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argparse
import os
import shutil
import sys
import http.server
import socketserver
from datetime import datetime
from pathlib import Path
from generator.site_builder import SiteBuilder
from generator.config import load_config
try:
    from livereload import Server
except ImportError:
    Server = None


def command_build(args):
    """Build the static site."""
    print("Building site...")
    try:
        # Determine if cache should be ignored
        if args.no_cache:
            cache_file = Path('.cache/markdown_cache.json')
            if cache_file.exists():
                os.remove(cache_file)
                print("Cache cleared.")
        
        builder = SiteBuilder(include_drafts=args.drafts)
        builder.build()

        print("Build complete.")
    except Exception as e:
        print(f"Error building site: {e}")
        sys.exit(1)

def command_serve(args):
    """Serve the static site locally."""
    config = load_config('config.yaml')
    port = args.port
    directory = config.output_dir
    
    # Check if output dir exists
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' not found. Have you run 'build'?")
        sys.exit(1)

    if Server:
        # Use livereload if available
        server = Server()
        
        # Define build function to run on changes
        def rebuild():
            print("Detected change, rebuilding...")
            builder = SiteBuilder(include_drafts=True) # Always include drafts in dev
            builder.build()
            print("Rebuild complete.")

        # Watch patterns
        server.watch('content/', rebuild)
        server.watch('templates/', rebuild)
        server.watch('static/', rebuild)
        server.watch('generator/', rebuild)
        server.watch('data/', rebuild)
        server.watch('config.yaml', rebuild)
        server.watch('files/', rebuild)
        
        print(f"Serving '{directory}' with Live Reload at http://localhost:{port}")
        server.serve(root=directory, port=port)
    else:
        # Fallback to standard http.server
        print("Warning: 'livereload' not installed. Live reload disabled.")
        print("Install it with: pip install livereload")
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

        try:
            with socketserver.TCPServer(("", port), Handler) as httpd:
                print(f"Serving '{directory}' at http://localhost:{port}")
                print("Press Ctrl+C to stop.")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server.")
        except OSError as e:
            print(f"Error starting server: {e}")
            sys.exit(1)

def command_new(args):
    """Create a new post."""
    title = args.title
    post_type = args.type
    
    slug = title.lower()
    
    # Swedish character replacements
    replacements = {
        'å': 'a',
        'ä': 'a',
        'ö': 'o',
        'Å': 'a',
        'Ä': 'a',
        'Ö': 'o'
    }
    for char, replacement in replacements.items():
        slug = slug.replace(char, replacement)
        
    slug = slug.replace(" ", "-") # Simple slugify
    import re
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Determine directory and filename structure
    if post_type == 'micro':
        target_dir = Path("content/micro")
        target_file = target_dir / f"{date_str}-{slug}.md"
        archetype_file = "archetypes/micro.md"
    elif post_type == 'reviews':
        target_dir = Path("content/reviews") / slug
        target_file = target_dir / "post.md"
        archetype_file = "archetypes/reviews.md"
    elif post_type == 'bookmarks':
        target_dir = Path("content/bookmarks") / slug
        target_file = target_dir / "post.md"
        archetype_file = "archetypes/bookmarks.md"
    else: # Default posts
        target_dir = Path("content/posts") / slug
        target_file = target_dir / "post.md"
        archetype_file = "archetypes/posts.md"

    if target_file.exists():
        print(f"Error: File '{target_file}' already exists.")
        sys.exit(1)
        
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and format archetype
        if not os.path.exists(archetype_file):
             # Fallback if archetype missing
             print(f"Warning: Archetype '{archetype_file}' not found. Using default.")
             content = f"---\ntitle: \"{title}\"\ndate: {datetime_str}\ndraft: true\n---\n"
        else:
             with open(archetype_file, 'r') as f:
                 template = f.read()
             
             # Format with available variables
             content = template.format(
                 title=title,
                 datetime=datetime_str,
                 date=date_str, # Just in case
                 # We can add more variables here later
             )
        
        with open(target_file, "w") as f:
            f.write(content)
        print(f"Created new {post_type}: {target_file}")
    except Exception as e:
        print(f"Error creating post: {e}")
        sys.exit(1)
    
    return # Return to skip the rest of the original function logic if any remains

    if target_file.exists():
        print(f"Error: File '{target_file}' already exists.")
        sys.exit(1)
        
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        
        content = f"{frontmatter}\n\nWrite your content here..."
        
        with open(target_file, "w") as f:
            f.write(content)
        print(f"Created new {post_type}: {target_file}")
    except Exception as e:
        print(f"Error creating post: {e}")
        sys.exit(1)

def command_clean(args):
    """Clean the output directory."""
    config = load_config('config.yaml')
    directory = config.output_dir
    
    if os.path.exists(directory):
        try:
            shutil.rmtree(directory)
            print(f"Removed '{directory}' directory.")
        except Exception as e:
            print(f"Error cleaning directory: {e}")
            sys.exit(1)
    else:
        print(f"Directory '{directory}' does not exist.")

def main():
    parser = argparse.ArgumentParser(description="Static Site Generator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Build command
    parser_build = subparsers.add_parser("build", help="Build the static site")
    parser_build.add_argument("--drafts", action="store_true", help="Include draft posts")
    parser_build.add_argument("--no-cache", action="store_true", help="Ignore cache and force full rebuild")
    
    # Serve command

    parser_serve = subparsers.add_parser("serve", help="Serve the site locally")
    parser_serve.add_argument("--port", type=int, default=8000, help="Port to serve on")
    
    # New command
    parser_new = subparsers.add_parser("new", help="Create a new post")
    parser_new.add_argument("title", help="Title of the new post")
    parser_new.add_argument("--type", "-t", choices=['posts', 'micro', 'reviews', 'bookmarks'], default='posts', help="Type of content")
    
    # Clean command
    parser_clean = subparsers.add_parser("clean", help="Clean the output directory")
    
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    args = parser.parse_args()
    
    if args.command == "build":
        command_build(args)
    elif args.command == "serve":
        command_serve(args)
    elif args.command == "new":
        command_new(args)
    elif args.command == "clean":
        command_clean(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
