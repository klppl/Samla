def render(shortname, text=None):
    """
    Renders a placeholder for an internal link that will be resolved by the SiteBuilder.
    Usage: {{< link "my-shortname" "Click Here" >}} or {{< link shortname="foo" >}}
    """
    if text:
        return f'<internal-link shortname="{shortname}">{text}</internal-link>'
    else:
        # If no text provided, we'll try to use the post title later
        return f'<internal-link shortname="{shortname}"></internal-link>'
