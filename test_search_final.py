import sys, os
os.chdir("/opt/javis/server")
sys.path.insert(0, "/opt/javis/server")
os.environ["SEARCH_API_KEY"] = "sk-8c36e0c75d9b406ebd0c748478a4c450"
from config import settings
k = settings.search_api_key
print("key ok, len=" + str(len(k)), flush=True)

import urllib.request, json
req = urllib.request.Request(
    "https://api.search.brave.com/res/v1/web/search?q=test&count=1",
    headers={"X-Subscription-Token": k, "Accept": "application/json"},
)
try:
    d = json.loads(urllib.request.urlopen(req, timeout=10).read())
    r = d.get("web", {}).get("results", [])
    print("Brave OK: " + str(len(r)) + " results", flush=True)
    for item in r[:2]:
        print("  - " + item.get("title", ""), flush=True)
except Exception as e:
    print("Brave FAIL: " + str(type(e).__name__) + ": " + str(e), flush=True)
