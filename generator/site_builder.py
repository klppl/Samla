import os
import shutil
import rcssmin
import rjsmin
import sass
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from PIL import Image
import json

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from .config import load_config, SiteConfig
from .content_loader import ContentLoader
from .renderer import Renderer
from .models import ContentItem, CONTENT_TYPES
from .data_loader import DataLoader

class SiteBuilder:
    """
    Orchestrates the entire static site generation process.
    
    This class ties together configuration, content loading, rendering, and asset management
    to produce the final static output. It follows a sequential build pipeline:
    Clean -> Prepare -> Load Content -> Render Posts -> Render Indices -> Generate Feeds/Sitemaps.
    """
    def __init__(self, config_path: str = 'config.yaml', include_drafts: bool = False):
        self.config = load_config(config_path)
        
        # Load Data
        data_loader = DataLoader('data')
        self.config.data = data_loader.load_data()
        
        self.renderer = Renderer('templates')
        
        # Load Locale
        self.locale_data = self._load_locale()
        
        # Inject translations
        if 'strings' in self.locale_data:
            self.renderer.env.globals['i18n'] = self.locale_data['strings']
            
        # Inject URL slugs
        self.slugs = self.locale_data.get('slugs', {})
        self.renderer.env.globals['slugs'] = self.slugs
            
        # Register Format Date Filter
        self.renderer.env.filters['localedate'] = self._localedate_filter
        
        # Pass jinja_env and site context (self.config) to ContentLoader
        self.content_loader = ContentLoader(
            self.config.content_dir, 
            include_drafts=include_drafts,
            jinja_env=self.renderer.env,
            site_context={'site': self.config},
            url_slugs=self.slugs
        )
        
        self.output_dir = Path(self.config.output_dir)
        self.include_drafts = include_drafts

    def _load_locale(self) -> Dict[str, Any]:
        """Load the locale file specified in config."""
        lang = self.config.language
        locale_path = Path(f'i18n/{lang}.yaml')
        
        if not locale_path.exists():
            print(f"Warning: Locale file '{locale_path}' not found. Falling back to empty.")
            return {}
            
        import yaml
        with open(locale_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _localedate_filter(self, date_obj, format_str='format'):
        """
        Jinja2 filter to format dates using the loaded locale.
        
        This allows for locale-specific date formatting (e.g. "1st January" vs "January 1").
        Usage: {{ post.date | localedate }} or {{ post.date | localedate('short') }}
        """
        if not date_obj:
            return ""
            
        if 'date' not in self.locale_data:
            return date_obj.strftime("%Y-%m-%d")

        date_config = self.locale_data['date']
        
        fmt_template = date_config.get(format_str, date_config.get('format', "{day} {month} {year}"))
        
        # Prepare replacements
        day = date_obj.day
        month_index = date_obj.month - 1 # 0-indexed
        day_index = date_obj.weekday() # 0 = Monday
        
        replacements = {
            "{day}": str(day),
            "{0day}": f"{day:02d}",
            "{year}": str(date_obj.year),
            "{month}": date_config['months'][month_index] if 'months' in date_config else str(date_obj.month),
            "{short_month}": date_config['short_months'][month_index] if 'short_months' in date_config else str(date_obj.month),
            "{weekday}": date_config['days'][day_index] if 'days' in date_config else str(day_index),
        }
        
        result = fmt_template
        for key, value in replacements.items():
            result = result.replace(key, value)
            
        return result
        
    def clean(self):
        """Clean the output directory."""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    def build(self):
        """
        Executes the full build process.
        This is the main entry point for the static site generation.
        """
        print(f"Building site '{self.config.title}'...")
        
        self.clean()
        self._prepare_output_directory()
        
        
        
        posts = self.content_loader.load_content()
        
        # Generate stats
        stats = {
            'total': len(posts),
            'micro': len([p for p in posts if p.type == 'micro']),
            'posts': len([p for p in posts if p.type == 'posts']),
            'reviews': len([p for p in posts if p.type == 'reviews']),
            'bookmarks': len([p for p in posts if p.type == 'bookmarks'])
        }
        
        print(f"✔ {stats['total']} total items")
        print(f"  ✔ {stats['micro']} micro")
        print(f"  ✔ {stats['posts']} posts")
        print(f"  ✔ {stats['reviews']} reviews")
        print(f"  ✔ {stats['bookmarks']} bookmarks")
        
        # Dynamic footer message
        import random
        footer_messages = [
            "Everything fades. Entropy is inevitable.",
            "Built with Python. Powered by Coffee.",
            "Static content is forever.",
            "Digital gardening in progress.",
            "Less is more."
        ]
        self.config.features['footer_message'] = random.choice(footer_messages)

        # Sort by date
        posts.sort(key=lambda x: x.date, reverse=True)
        
        # Determine last updated (based on newest post)
        if posts:
            self.config.last_updated = posts[0].date
            
        # Store posts for related calculation
        self.all_posts = posts
        self.shortname_map = {p.shortname: p for p in posts if p.shortname}


        for post in posts:
            self._render_post(post)
            
        # Render Index (Home Stream)
        # Filter posts based on feature flags
        index_posts = []
        for post in posts:
            if post.type == 'reviews' and not self.config.features.get('reviews_in_index', True):
                continue
            if post.type == 'bookmarks' and not self.config.features.get('bookmarks_in_index', True):
                continue
            if post.hide_from_home:
                continue
            index_posts.append(post)
            
        self._render_index(index_posts)
        
        self._render_sections(posts)

        if self.config.features.get('tags'):
            self._render_tags(posts)
        
        if self.config.features.get('categories'):
            self._render_categories(posts)
        
        if self.config.features.get('rss'):
            self._generate_rss(posts)
            
        self._generate_sitemap(posts)
        
        self._copy_static_assets()
        self._copy_content_assets()
        
        self._generate_404()
        
        self._generate_search_index(posts)
        
        self._generate_search_page()
        
        self._generate_humans_txt()
        
        print("Build complete.")



    def _prepare_output_directory(self):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)

    def _copy_static_assets(self):
        # Copy root files
        if os.path.exists(self.config.files_dir):
            shutil.copytree(self.config.files_dir, self.output_dir, dirs_exist_ok=True)

        # Copy static assets
        static_src = Path('static')
        if static_src.exists():
            static_dst = self.output_dir / 'static'
            # Custom copy to allow processing
            if static_dst.exists():
                 shutil.rmtree(static_dst)
            static_dst.mkdir(parents=True)

            for root, dirs, files in os.walk(static_src):
                # Calculate relative path
                rel_path = Path(root).relative_to(static_src)
                target_dir = static_dst / rel_path
                target_dir.mkdir(parents=True, exist_ok=True)
                
                for file in files:
                    src_file = Path(root) / file
                    dst_file = target_dir / file
                    
                    if file.endswith('.css'):
                        with open(src_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        minified = rcssmin.cssmin(content)
                        with open(dst_file, 'w', encoding='utf-8') as f:
                            f.write(minified)
                    elif file.endswith('.scss'):
                        # Skip partials
                        if file.startswith('_'):
                            continue
                            
                        try:
                            # Compile Sass with minification
                            compiled_css = sass.compile(filename=str(src_file), output_style='compressed')
                            
                            # Save as .css
                            css_dst = dst_file.with_suffix('.css')
                            with open(css_dst, 'w', encoding='utf-8') as f:
                                f.write(compiled_css)
                        except Exception as e:
                            print(f"Error compiling Sass {src_file}: {e}")

                    elif file.endswith('.js'):
                        # rjsmin doesn't handle some modern JS features carefully, 
                        # but site_builder.py is python. rjsmin is python binding.
                        # Basic JS minification.
                        with open(src_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        minified = rjsmin.jsmin(content)
                        with open(dst_file, 'w', encoding='utf-8') as f:
                            f.write(minified)
                    elif file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        # Image Optimization
                        try:
                            with Image.open(src_file) as img:
                                # Resize if larger than 1200px
                                if img.width > 1200:
                                    ratio = 1200 / img.width
                                    new_height = int(img.height * ratio)
                                    img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
                                
                                # Save optimized original
                                img.save(dst_file, optimize=True, quality=85)
                                
                                # Generate WebP
                                webp_path = dst_file.with_suffix('.webp')
                                img.save(webp_path, 'WEBP', quality=85)
                        except Exception as e:
                            print(f"Error optimizing image {src_file}: {e}")
                            shutil.copy2(src_file, dst_file)
                    else:
                        shutil.copy2(src_file, dst_file)

    def _copy_content_assets(self):
        """Copy non-markdown files from content directory to output directory."""
        content_path = Path(self.config.content_dir)
        if not content_path.exists():
            return

        for root, _, files in os.walk(content_path):
            for file in files:
                if file.endswith('.md'):
                    continue
                
                src_path = Path(root) / file
                rel_path = src_path.relative_to(content_path)
                
                # Localize the first part of the path (section) if applicable
                parts = list(rel_path.parts)
                if parts and parts[0] in self.slugs:
                    parts[0] = self.slugs[parts[0]]
                    rel_path = Path(*parts)
                
                dst_path = self.output_dir / rel_path
                
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)

    def _render_post(self, post: ContentItem):
        # Create directory: {output_dir}/{section}/{slug}/
        # post.url is like /{section}/{slug}/
        # So we strip leading slash
        rel_path = post.url.strip('/')
        post_dir = self.output_dir / rel_path
        post_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine template
        # Try to find {type}.html, else fall back to post.html
        template_name = f"{post.type}.html"
        if not os.path.exists(f"templates/{template_name}"):
             template_name = 'post.html'
        
        # Get related posts
        related_posts = self._get_related_posts(post)

        canonical_url = f"{self.config.base_url}{post.url}"
        html = self._render_template(template_name, {
            'site': self.config,
            'post': post,
            'canonical_url': canonical_url,
            'related_posts': related_posts
        }, current_url=post.url)
        
        with open(post_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(html)

    def _render_index(self, posts: List[ContentItem]):
        # Pagination Logic
        per_page = self.config.posts_per_page
        total_posts = len(posts)
        total_pages = (total_posts + per_page - 1) // per_page
        
        for page_num in range(1, total_pages + 1):
            start = (page_num - 1) * per_page
            end = start + per_page
            page_posts = posts[start:end]
            
            # Pagination context
            pagination = {
                'current_page': page_num,
                'total_pages': total_pages,
                'has_prev': page_num > 1,
                'has_next': page_num < total_pages,
                'prev_url': f'/page/{page_num - 1}/' if page_num > 2 else '/',
                'next_url': f'/page/{page_num + 1}/'
            }
            
            # Helper to generate page URL
            def get_page_url(p):
                return '/' if p == 1 else f'/page/{p}/'

            # Pagination Window Logic
            page_window = []
            if total_pages <= 7:
                page_window = list(range(1, total_pages + 1))
            else:
                # Always show first, last, and window around current
                window_set = {1, total_pages}
                for i in range(page_num - 2, page_num + 3):
                    if 1 <= i <= total_pages:
                        window_set.add(i)
                sorted_pages = sorted(list(window_set))
                
                # Insert gaps
                last_p = 0
                for p in sorted_pages:
                    if last_p > 0 and p - last_p > 1:
                        page_window.append(None) # Gap
                    page_window.append(p)
                    last_p = p

            pagination['pages'] = []
            for p in page_window:
                if p is None:
                    pagination['pages'].append({'num': None, 'url': None, 'current': False})
                else:
                    pagination['pages'].append({
                        'num': p,
                        'url': get_page_url(p),
                        'current': p == page_num
                    })
            
            # Determine output path and current URL
            if page_num == 1:
                output_path = self.output_dir / 'index.html'
                current_url = '/'
                canonical_url = f"{self.config.base_url}/"
            else:
                page_dir = self.output_dir / 'page' / str(page_num)
                page_dir.mkdir(parents=True, exist_ok=True)
                output_path = page_dir / 'index.html'
                current_url = f'/page/{page_num}/'
                canonical_url = f"{self.config.base_url}/page/{page_num}/"

            html = self._render_template('index.html', {
                'site': self.config,
                'posts': page_posts,
                'title': self.config.title,
                'pagination': pagination,
                'canonical_url': canonical_url
            }, current_url=current_url)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

    def _render_sections(self, posts: List[ContentItem]):
        # Group by type
        sections = {ctype: [] for ctype in CONTENT_TYPES.keys()}
        for post in posts:
            if post.type not in sections:
                sections[post.type] = []
            sections[post.type].append(post)
        
        for section_name, section_posts in sections.items():
            # Translate section name for URL/Folder
            slugs = self.locale_data.get('slugs', {})
            url_section = slugs.get(section_name, section_name)

            section_dir = self.output_dir / url_section
            section_dir.mkdir(parents=True, exist_ok=True)
            
            current_url = f"/{url_section}/"

            # Translate Title
            strings = self.locale_data.get('strings', {})
            # Try to find specific content type translation, fall back to capitalized name
            title = strings.get(section_name, section_name.capitalize())

            html = self._render_template('section.html', {
                'site': self.config,
                'posts': section_posts,
                'title': title,
                'section': section_name,
                'canonical_url': f"{self.config.base_url}{current_url}"
            }, current_url=current_url)
            
            with open(section_dir / 'index.html', 'w', encoding='utf-8') as f:
                f.write(html)

    def _render_tags(self, posts: List[ContentItem]):
        # Collect tags
        tags = {}
        for post in posts:
            for tag in post.tags:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(post)
        
        # Render individual tag pages
        tags_dir = self.output_dir / 'tags'
        tags_dir.mkdir(exist_ok=True)
        
        for tag, tag_posts in tags.items():
            tag_slug_dir = tags_dir / tag
            tag_slug_dir.mkdir(exist_ok=True)
            
            current_url = f"/tags/{tag}/"
            
            # Localized Title
            tag_label = self.locale_data.get('strings', {}).get('tags', 'Tag')
            page_title = f"{tag_label}: {tag}"
            
            html = self._render_template('taxonomy.html', {
                'site': self.config,
                'posts': tag_posts,
                'title': page_title,
                'taxonomy_type': 'Tag',
                'taxonomy_name': tag,
                'canonical_url': f"{self.config.base_url}{current_url}"
            }, current_url=current_url)
            
            with open(tag_slug_dir / 'index.html', 'w', encoding='utf-8') as f:
                f.write(html)
                
        # Optional: Render tag list page
        
    def _render_categories(self, posts: List[ContentItem]):
        # Collect categories
        categories = {}
        for post in posts:
            if post.category:
                cat = post.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(post)
        
        cat_dir = self.output_dir / 'categories'
        cat_dir.mkdir(exist_ok=True)
        
        for cat, cat_posts in categories.items():
            # simple slugify
            cat_slug = cat.lower().replace(' ', '-')
            
            cat_slug_dir = cat_dir / cat_slug
            cat_slug_dir.mkdir(exist_ok=True)
            
            current_url = f"/categories/{cat_slug}/"
            
            # Localized Title
            cat_label = self.locale_data.get('strings', {}).get('categories', 'Category')
            page_title = f"{cat_label}: {cat}"

            html = self._render_template('taxonomy.html', {
                'site': self.config,
                'posts': cat_posts,
                'title': page_title,
                'taxonomy_type': 'Category',
                'taxonomy_name': cat,
                'canonical_url': f"{self.config.base_url}{current_url}"
            }, current_url=current_url)
            
            with open(cat_slug_dir / 'index.html', 'w', encoding='utf-8') as f:
                f.write(html)

    def _generate_rss(self, posts: List[ContentItem]):
        from datetime import datetime
        
        # RSS links should be absolute for readers, using base_url if available
        # But here we just render the XML.
        rss_content = self.renderer.render('rss.xml', {
            'site': self.config,
            'posts': posts,
            'now': datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        })
        
        with open(self.output_dir / 'rss.xml', 'w', encoding='utf-8') as f:
            f.write(rss_content)

    def _generate_sitemap(self, posts: List[ContentItem]):
        # Sitemap links must be absolute
        sitemap_content = self.renderer.render('sitemap.xml', {
            'site': self.config,
            'posts': posts
        })
        
        with open(self.output_dir / 'sitemap.xml', 'w', encoding='utf-8') as f:
            f.write(sitemap_content)


    def _generate_404(self):
        # 404 pages often sit at root, but sometimes are served from anywhere.
        # We'll treat it as being at root for relative links.
        current_url = "/404.html"
        html = self._render_template('404.html', {
            'site': self.config,
            'title': 'Page Not Found',
            'canonical_url': f"{self.config.base_url}/404.html"
        }, current_url=current_url)
        
        with open(self.output_dir / '404.html', 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_search_index(self, posts: List[ContentItem]):
        """Generate a JSON index for client-side search."""
        search_index = []
        for post in posts:
            # Strip HTML for plain text content
            soup = BeautifulSoup(post.content, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            
            search_index.append({
                'title': post.title,
                'url': post.url,
                'date': post.date.strftime('%Y-%m-%d'),
                'tags': post.tags,
                'content': text_content,
                'type': post.type
            })
            
        with open(self.output_dir / 'search.json', 'w', encoding='utf-8') as f:
            json.dump(search_index, f, ensure_ascii=False)

    def _generate_search_page(self):
        """Render the static search page."""
        search_dir = self.output_dir / 'search'
        search_dir.mkdir(parents=True, exist_ok=True)
        
        current_url = "/search/"
        html = self._render_template('search.html', {
            'site': self.config,
            'title': 'Search',
            'canonical_url': f"{self.config.base_url}/search/"
        }, current_url=current_url)
        
        with open(search_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(html)

    def _get_related_posts(self, current_post: ContentItem, limit: int = 3) -> List[ContentItem]:
        if not hasattr(self, 'all_posts') or not current_post.tags:
            return []
        
        candidates = []
        current_tags = set(current_post.tags)
        
        for post in self.all_posts:
            if post == current_post:
                continue
            
            # Calculate overlap
            post_tags = set(post.tags)
            overlap = len(current_tags.intersection(post_tags))
            
            if overlap > 0:
                candidates.append((overlap, post))
        
        # Sort by overlap (desc), then date (desc)
        candidates.sort(key=lambda x: (x[0], x[1].date), reverse=True)
        
        return [c[1] for c in candidates[:limit]]

    def _get_relative_path(self, from_url: str, to_url: str) -> str:
        """
        Calculate relative path from current URL to target URL.
        Useful for fully portable static sites (subfolder deployment).
        """
        # Ensure URLs start with / for logic consistency
        if not from_url.startswith('/'): from_url = '/' + from_url
        if not to_url.startswith('/'): to_url = '/' + to_url

        # Remove file name from from_url to get source directory
        # If from_url ends with /, it is a directory.
        # If it doesn't (like /index.html or /404.html), we need dirname.
        if from_url.endswith('/'):
            from_dir = from_url
        else:
            from_dir = os.path.dirname(from_url)

        # Remove leading slash for os.path.relpath to work
        from_dir = from_dir.lstrip('/') or '.'
        to_url = to_url.lstrip('/') or '.'

        try:
            rel_path = os.path.relpath(to_url, from_dir)
            return rel_path
        except ValueError:
            return to_url

    def _render_template(self, template_name: str, context: Dict[str, Any], current_url: str = None) -> str:
        # Inject rel_url helper
        if current_url:
            def rel_url(target):
                # If target is external or anchor, return as is
                if '://' in target or target.startswith('#') or target.startswith('mailto:'):
                    return target
                return self._get_relative_path(current_url, target)
            
            context['rel_url'] = rel_url
        
        html = self.renderer.render(template_name, context)
        html = self._resolve_internal_links(html, current_url)
        return self._process_links(html)

    def _process_links(self, html: str) -> str:
        if not self.config.base_url:
            return html
            
        soup = BeautifulSoup(html, 'html.parser')
        base_netloc = urlparse(self.config.base_url).netloc
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            try:
                parsed = urlparse(href)
                # Check if absolute URL and different domain
                if parsed.scheme and parsed.netloc and parsed.netloc != base_netloc:
                    # Parse existing query params
                    query_params = parse_qs(parsed.query)
                    
                    # Add ref param
                    query_params['ref'] = [base_netloc]
                    
                    # Reconstruct URL
                    new_query = urlencode(query_params, doseq=True)
                    new_href = urlunparse((
                        parsed.scheme,
                        parsed.netloc,
                        parsed.path,
                        parsed.params,
                        new_query,
                        parsed.fragment
                    ))
                    
                    a_tag['href'] = new_href
            except Exception as e:
                # Ignore malformed URLs
                pass
                
        return str(soup)

    def _resolve_internal_links(self, html: str, current_url: str = None) -> str:
        if '<internal-link' not in html:
            return html
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for tag in soup.find_all('internal-link'):
            shortname = tag.get('shortname')
            target_post = self.shortname_map.get(shortname)
            
            if target_post:
                href = target_post.url
                if current_url:
                    href = self._get_relative_path(current_url, href)
                
                new_tag = soup.new_tag('a', href=href)
                # If tag has Content, use it. Else use Post Title.
                if tag.string:
                    new_tag.string = tag.string
                else:
                    new_tag.string = target_post.title
                
                tag.replace_with(new_tag)
            else:
                # Warning for broken link
                new_tag = soup.new_tag('span', style="color:red; font-weight:bold;")
                new_tag.string = f"[Broken Link: {shortname}]"
                tag.replace_with(new_tag)
                print(f"Warning: Could not resolve internal link '{shortname}'")
        
        return str(soup)

    def _generate_humans_txt(self):
        """Generate/Override humans.txt based on config (Generic Version)."""
        humans = self.config.humans
        if not humans:
            return

        lines = []

        for section_name, section_data in humans.items():
            # Section Header (e.g. /* TEAM */)
            lines.append(f"/* {section_name.upper()} */")
            
            # Handle List of items (e.g. Team members, Thanks list)
            if isinstance(section_data, list):
                for item in section_data:
                    if isinstance(item, dict):
                        # List of objects (Team members)
                        for key, value in item.items():
                            lines.append(f"{key.capitalize()}: {value}")
                        lines.append("") # Separator between items
                    else:
                         # Simple list (Thanks)
                         lines.append(str(item))
                if isinstance(section_data[0], str):
                     lines.append("") # Separator after simple list

            # Handle Dictionary (e.g. Site, Contact)
            elif isinstance(section_data, dict):
                for key, value in section_data.items():
                    # Handle list values (e.g. standards: [...])
                    if isinstance(value, list):
                        lines.append(f"{key.capitalize()}: {', '.join(str(v) for v in value)}")
                    else:
                        lines.append(f"{key.capitalize()}: {value}")
                lines.append("")

        content = "\n".join(lines).strip()
        
        with open(self.output_dir / 'humans.txt', 'w', encoding='utf-8') as f:
            f.write(content)

