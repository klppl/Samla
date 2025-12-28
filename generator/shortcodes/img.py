def render(src: str, alt: str = "", caption: str = "", width: str = "100%", cls: str = ""):
    """
    Renders an image, optionally with a caption using <figure>.
    Usage: 
    {{< img src="/path/to/image.jpg" alt="Description" >}}
    {{< img "/path/to/image.jpg" "Description" >}}
    """
    
    # Clean up arguments
    if not alt:
        alt = "Image"
        
    style = f"max-width: {width}; height: auto; border-radius: 8px;"
    img_tag = f'<img src="{src}" alt="{alt}" class="{cls}" style="{style}" loading="lazy">'
    
    if caption:
        html = f"""
<figure style="margin: 1.5rem 0; text-align: center;">
    {img_tag}
    <figcaption style="margin-top: 0.5rem; color: #666; font-style: italic; font-size: 0.9em;">
        {caption}
    </figcaption>
</figure>
"""
    else:
        # Just the image, perhaps wrapped for spacing
        html = f"""
<div style="margin: 1.5rem 0;">
    {img_tag}
</div>
"""
    return html
