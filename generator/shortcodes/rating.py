def render(score: str, max_score: str = "10"):
    """
    Renders a star rating.
    Usage: {{< rating 9.5 >}} or {{< rating 4 5 >}}
    """
    try:
        val = float(score)
        maximum = float(max_score)
        
        # Normalize to 5-star scale
        normalized = (val / maximum) * 5
        
        full = int(normalized)
        half = (normalized - full) >= 0.5
        empty = 5 - full - (1 if half else 0)
        
        stars = "★" * full + ("⯨" if half else "") + "☆" * empty
        
        return f'<span class="review-stars" title="{val}/{maximum}">{stars}</span>'
    except ValueError:
        return f'<!-- Invalid rating: {score}/{max_score} -->'
