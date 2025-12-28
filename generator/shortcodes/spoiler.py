def render(title: str = "Spoiler", content: str = ""):
    """
    Renders a spoiler block with hidden content.
    Usage: {{< spoiler "Title" >}} Content... {{< /spoiler >}}
    """
    return f"""
<details markdown="1" style="border: 1px solid #ddd; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
<summary style="cursor: pointer; font-weight: bold; margin-bottom: 1rem;">{title}</summary>
{content}
</details>
"""
