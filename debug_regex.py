import re
import shlex

pattern = re.compile(r'{{<\s*([\w-]+)\s*(.*?)\s*>}}(?:(.*?){{<\s*/\1\s*>}})?', re.DOTALL)

content = 'Du kan mejla mig på {{< email "alexander@klippel.se" >}}.'

match = pattern.search(content)
if match:
    print(f"MATCH: {match.group(0)}")
    print(f"Name: {match.group(1)}")
    print(f"Args: {match.group(2)}")
    try:
        args = shlex.split(match.group(2))
        print(f"Parsed Args: {args}")
    except Exception as e:
        print(f"Shlex Error: {e}")
else:
    print("NO MATCH")
