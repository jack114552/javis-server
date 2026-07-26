import urllib.request, json, sys, os
os.chdir('/opt/javis/server')
sys.path.insert(0, '/opt/javis/server')
from config import settings
key = settings.search_api_key
print(f'key length: {len(key)}, first 10: {key[:10]}')
try:
    req = urllib.request.Request(
        'https://api.search.brave.com/res/v1/web/search?q=test&count=1',
        headers={'X-Subscription-Token': key, 'Accept': 'application/json'},
    )
    d = json.loads(urllib.request.urlopen(req, timeout=10).read())
    r = d.get('web', {}).get('results', [])
    print(f'Brave OK: {len(r)} results')
except Exception as e:
    print(f'Brave FAIL: {type(e).__name__}: {e}')
