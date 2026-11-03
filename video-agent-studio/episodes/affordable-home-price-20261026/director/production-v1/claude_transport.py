"""Read only the terminal result event from Claude JSON or JSONL output."""
import json

def parse_result(raw):
    try:
        value=json.loads(raw)
    except json.JSONDecodeError:
        value=None
    if isinstance(value,dict) and value.get('type')=='result':
        return value
    results=[]
    for line in raw.splitlines():
        try:
            value=json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value,dict) and value.get('type')=='result':
            results.append(value)
    if not results:
        raise ValueError('Claude terminal result event missing')
    return results[-1]
