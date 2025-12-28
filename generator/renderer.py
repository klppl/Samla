from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

class Renderer:
    def __init__(self, templates_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self._register_filters()

    def _register_filters(self):
        def format_date(value: datetime, fmt: str = "%Y-%m-%d"):
            if isinstance(value, datetime):
                return value.strftime(fmt)
            return value
        
        self.env.filters['date'] = format_date
        
        def relative_time(value: datetime) -> str:
            """Formats a datetime as a relative time string (e.g. '2 days ago')."""
            from datetime import date
            
            # Handle date objects (that aren't datetime)
            if type(value) is date:
                 value = datetime.combine(value, datetime.min.time())
            
            if not isinstance(value, datetime):
                return value
            
            now = datetime.now()
            diff = now - value
            
            seconds = diff.total_seconds()
            
            if seconds < 60:
                return "just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif seconds < 604800:
                days = int(seconds / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
            elif seconds < 2592000:
                weeks = int(seconds / 604800)
                return f"{weeks} week{'s' if weeks != 1 else ''} ago"
            elif seconds < 31536000:
                months = int(seconds / 2592000)
                return f"{months} month{'s' if months != 1 else ''} ago"
            else:
                years = int(seconds / 31536000)
                return f"{years} year{'s' if years != 1 else ''} ago"

        self.env.filters['relative_time'] = relative_time
        
        def inject_permalink(content: str, url: str) -> str:
            """Injects a permalink anchor at the end of the last paragraph."""
            if not content:
                return content
                
            permalink_html = f' <a href="{url}" class="micro-permalink" title="Permalink">#</a>'
            
            # Try to insert before the closing </p> tag
            if '</p>' in content:
                # Find the last occurrence of </p>
                last_p_index = content.rfind('</p>')
                return content[:last_p_index] + permalink_html + content[last_p_index:]
            
            # If no p tag, just append
            return content + permalink_html

        self.env.filters['inject_permalink'] = inject_permalink

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)
