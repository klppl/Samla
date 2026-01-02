from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import List, Optional, Dict, Any

# Registry for content types
# This registry pattern allows for easy extension of content types without modifying the core loader logic.
# New content types can be added by decorating a class with @register_content_type('type_name').
CONTENT_TYPES = {}

def register_content_type(name):
    def decorator(cls):
        CONTENT_TYPES[name] = cls
        return cls
    return decorator

@dataclass
class MenuLink:
    name: str
    url: str
    icon: str = ""
    type: Optional[str] = None
    break_before: bool = False

@dataclass
class SiteConfig:
    """
    Global configuration for the static site.
    
    Attributes:
        title (str): The main title of the website.
        base_url (str): The specific URL where the site will be hosted. 
                        Used for generating canonical URLs and absolute links.
    """
    title: str
    subtitle: str
    base_url: str
    timezone: str
    language: str
    menu: List[MenuLink]
    content_dir: str
    output_dir: str
    posts_per_page: int
    features: Dict[str, bool]
    social: Dict[str, str]
    background_image: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[datetime] = None
    files_dir: str = 'files'
    humans: Dict[str, Any] = field(default_factory=dict)
    frontpage_filter: Dict[str, bool] = field(default_factory=dict)
    index_filter: Dict[str, bool] = field(default_factory=dict)

@dataclass
class ContentItem:
    """
    Base class for all content items (posts, pages, reviews, etc.).
    
    This class handles standard metadata found in all Markdown frontmatter,
    such as title, date, and tags. Subclasses should extend this to add
    type-specific fields.
    """
    title: str
    date: datetime
    slug: str
    url: str
    content: str
    type: str  # 'micro', 'blog', 'reviews', 'bookmarks'
    frontmatter: Dict
    path: str
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    shortname: Optional[str] = None
    hide_from_home: bool = False
    
    # Defaults (can be overridden by subclasses)
    default_icon = "\U0001F4AC" # 💬

    @property
    def icon(self) -> str:
        # Get emoji from frontmatter, defaulting to None if key missing
        emoji = self.frontmatter.get('emoji')
        # Return emoji if it exists and is not None/Empty, otherwise default
        return emoji if emoji else self.default_icon

    @classmethod
    def from_frontmatter(cls, frontmatter: Dict, **kwargs):
        """
        Factory method to create an instance from frontmatter and standard args.
        Automatically maps frontmatter keys to dataclass fields.
        """
        init_kwargs = kwargs.copy()
        
        init_kwargs['frontmatter'] = frontmatter
        
        valid_field_names = {f.name for f in fields(cls)}
        
        for field_name in valid_field_names:
            if field_name not in init_kwargs:
                # Try to find it in frontmatter
                if field_name in frontmatter:
                    init_kwargs[field_name] = frontmatter[field_name]
                    
        # Allow subclasses to hook in for custom logic
        init_kwargs = cls.process_init_kwargs(init_kwargs, frontmatter)
        
        return cls(**init_kwargs)

    @classmethod
    def process_init_kwargs(cls, kwargs, frontmatter):
        """Hook for subclasses to modify kwargs before init."""
        return kwargs

@register_content_type('micro')
@dataclass
class MicroPost(ContentItem):
    pass

@register_content_type('posts')
@dataclass
class BlogPost(ContentItem):
    pass

@register_content_type('reviews')
@dataclass
class Review(ContentItem):
    rating: Optional[float] = None


    @property
    def star_string(self) -> str:
        if self.rating is None:
            return ""
        # Convert 10-scale to 5-scale
        score = self.rating / 2
        full = int(score)
        half = score - full >= 0.5
        empty = 5 - full - (1 if half else 0)
        return "★" * full + ("⯨" if half else "") + "☆" * empty

@register_content_type('bookmarks')
@dataclass
class Bookmark(ContentItem):
    link: Optional[str] = None
    domain: Optional[str] = None

    @classmethod
    def process_init_kwargs(cls, kwargs, frontmatter):
        # Handle the domain parsing custom logic
        link = frontmatter.get('link')
        if link:
            from urllib.parse import urlparse
            try:
                domain = urlparse(link).netloc
                if domain.startswith('www.'):
                    domain = domain[4:]
                kwargs['domain'] = domain
            except:
                pass
             
        return kwargs


@register_content_type('music')
@dataclass
class Music(Bookmark):
    @property
    def has_single_embed(self) -> bool:
        # Check if there is exactly one iframe
        # We look for <iframe because counting content.count('<iframe') is reliable enough for generated HTML
        return self.content.count('<iframe') == 1

@register_content_type('pages')
@dataclass
class Page(ContentItem):
    pass
