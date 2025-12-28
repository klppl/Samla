from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import List, Optional, Dict, Any

# Registry for content types
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

@dataclass
class SiteConfig:
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

@dataclass
class ContentItem:
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
        # Start with base arguments
        init_kwargs = kwargs.copy()
        
        # Add frontmatter itself
        init_kwargs['frontmatter'] = frontmatter
        
        # Inspect the class to find what extra fields it supports
        # We use dataclasses.fields to get all fields including inherited ones
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
    watched_on: Optional[str] = None

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
    via: Optional[str] = None
    why: Optional[str] = None
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
        
        # Mapping variations
        if 'why_bookmarked' in frontmatter and 'why' not in kwargs:
             kwargs['why'] = frontmatter['why_bookmarked']
             
        return kwargs
