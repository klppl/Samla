import os
import markdown
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime, date

from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
from .models import ContentItem, MicroPost, BlogPost, Review, Bookmark, CONTENT_TYPES
from .shortcode_manager import ShortcodeManager
from .cache import CacheManager
import frontmatter as fm



class ContentLoader:
    """
    Handles the loading, parsing, and processing of Markdown content files.
    
    This class is responsible for:
    1. Parsing YAML frontmatter.
    2. Processing shortcodes.
    3. Rendering Jinja2 templates embedded in Markdown.
    4. Caching results to speed up subsequent builds.
    """
    def __init__(self, content_dir: str, include_drafts: bool = False, jinja_env=None, site_context=None, url_slugs=None):
        self.content_dir = Path(content_dir)
        self.include_drafts = include_drafts
        self.shortcode_manager = ShortcodeManager()
        self.cache_manager = CacheManager()
        self.jinja_env = jinja_env
        self.site_context = site_context
        self.url_slugs = url_slugs or {}

    def load_content(self) -> List[ContentItem]:
        """
        Traverses the content directory and loads all valid content items.
        
        Returns:
            List[ContentItem]: A list of parsed content items, sorted by date (newest first).
        """

        posts = []
        # Walk through top-level directories which are 'sections' or 'types'
        if not self.content_dir.exists():
            return []

        for section in os.listdir(self.content_dir):
            section_path = self.content_dir / section
            if not section_path.is_dir():
                continue
            
            # Now walk through slug directories OR files
            for item in os.listdir(section_path):
                item_path = section_path / item
                
                if item_path.is_dir():
                    post_file = item_path / 'post.md'
                    if post_file.exists():
                        slug = item
                        post = self._parse_post(post_file, section, slug)
                        if post:
                            posts.append(post)
                            
                elif item_path.is_file() and item.endswith('.md'):
                    slug = item[:-3] # remove .md
                    post = self._parse_post(item_path, section, slug)
                    if post:
                        posts.append(post)
        
        # Sort by date, newest first
        posts.sort(key=lambda x: x.date, reverse=True)
        
        # Save cache
        self.cache_manager.save()
        
        return posts


    def _parse_post(self, file_path: Path, section: str, slug: str) -> Optional[ContentItem]:
        try:
            mtime = file_path.stat().st_mtime
            
            # Check cache with file modification time.
            # If the file hasn't changed since the last build, we return the cached HTML
            # to avoid expensive re-parsing of Markdown and Shortcodes.
            cached_data = self.cache_manager.get(str(file_path), mtime)
            
            if cached_data:
                html_content = cached_data['html']
                frontmatter = cached_data['frontmatter']
            else:
                post_data = fm.load(file_path)
                content_raw = post_data.content
                frontmatter = post_data.metadata
                
                content_with_shortcodes = self.shortcode_manager.process(content_raw)
                
                if self.jinja_env and self.site_context:
                    try:
                        # Create a template from the content with shortcodes already expanded
                        template = self.jinja_env.from_string(content_with_shortcodes)
                        # Render it with the site context
                        content_raw = template.render(**self.site_context)
                    except Exception as e:
                        print(f"Error rendering Liquid/Jinja in {file_path}: {e}")
                        # Fallback to content with shortcodes if rendering fails
                        content_raw = content_with_shortcodes
                else:
                    content_raw = content_with_shortcodes
                
                html_content = markdown.markdown(content_raw, extensions=['fenced_code', 'tables', 'codehilite', 'extra'])
                
                # Prepare frontmatter for cache by serializing datetimes
                frontmatter_serializable = {}
                for k, v in frontmatter.items():
                    if isinstance(v, (datetime, date)):
                        frontmatter_serializable[k] = v.isoformat()
                    else:
                        frontmatter_serializable[k] = v
                        
                self.cache_manager.set(str(file_path), mtime, {
                    'html': html_content,
                    'frontmatter': frontmatter_serializable
                })
            
            
            
            # Draft check
            if frontmatter.get('draft') and not self.include_drafts:
                return None
            
            # Date handling (Re-parse if coming from cache/string)
            date_val = frontmatter.get('date')
            if isinstance(date_val, str):
                try:
                    date_obj = date_parser.parse(date_val)
                except:
                    date_obj = datetime.now()
            elif isinstance(date_val, datetime):
                # YAML loader might auto-parse dates
                date_obj = date_val
            elif isinstance(date_val, date):
                # Handle plain date objects
                date_obj = datetime.combine(date_val, datetime.min.time())
            else:
                date_obj = datetime.now()

            # URL construction: /{localized_section}/{slug}/
            if section == 'pages':
                url = f"/{slug}/"
            else:
                url_section = self.url_slugs.get(section, section)
                url = f"/{url_section}/{slug}/"
            
            # Tags and Categories
            tags_raw = frontmatter.get('tags', [])
            if isinstance(tags_raw, str):
                tags = [t.strip() for t in tags_raw.split(',')]
            else:
                tags = tags_raw
            
            # Normalize tags
            tags = [str(t).lower() for t in tags]
            
            category = frontmatter.get('category')
            
            # Determine subclass and specific fields
            # Determine subclass
            # Use Registry
            model_class = CONTENT_TYPES.get(section, BlogPost) # Default to BlogPost
            
            # Prepare base kwargs
            base_kwargs = {
                'title': frontmatter.get('title', 'Untitled'),
                'date': date_obj,
                'slug': slug,
                'url': url,
                'content': html_content,
                'type': section,
                'path': str(file_path),
                'tags': tags,
                'category': category
            }
            
            # Create instance using factory
            return model_class.from_frontmatter(frontmatter, **base_kwargs)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
