import random
import string

def render(address, text=None):
    """
    Renders an obfuscated email link using JavaScript injection.
    
    Usage:
    {{< email "user@example.com" >}}
    {{< email "user@example.com" "Email Me" >}}
    """
    if not text:
        text = address
        
    # Helper to encode string to JS char codes
    def encode_to_js(s):
        return "+".join([f"String.fromCharCode({ord(c)})" for c in s])
        
    js_address = encode_to_js(address)
    js_text = encode_to_js(text)
    
    # Generate unique ID for this instance
    uid = ''.join(random.choice(string.ascii_letters) for _ in range(8))
    
    return f"""
    <span id="mail-{uid}"></span>
    <script>
    (function() {{
        var addr = {js_address};
        var txt = {js_text};
        document.getElementById('mail-{uid}').innerHTML = '<a href="mailto:' + addr + '">' + txt + '</a>';
    }})();
    </script>
    <noscript>(Enable JavaScript to view email)</noscript>
    """
