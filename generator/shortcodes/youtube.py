def render(id: str, title: str = "YouTube Video", autoplay: str = "false"):
    """
    Renders a responsive YouTube embed.
    Usage: {{< youtube id="dQw4w9WgXcQ" >}} or {{< youtube "dQw4w9WgXcQ" >}}
    """

    
    # Handle string 'true'/'false' for autoplay if passed from shortcode
    autoplay_param = 1 if str(autoplay).lower() == 'true' else 0
    
    html = f"""
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 8px; margin-bottom: 1.5rem;">
    <iframe 
        src="https://www.youtube.com/embed/{id}?autoplay={autoplay_param}" 
        title="{title}"

        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" 
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
        allowfullscreen>
    </iframe>
</div>
"""
    return html
