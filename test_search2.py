import urllib.request, json, sys

key = "sk-8c3…c450"
query = sys.argv[1] if len(sys.argv) > 1 else "test"

# Brave
try:
    req = urllib.request.Request(
        f"https://api.search.brave.com/res/v1/web/search?q={query}&count=3",
        headers={"X-Subscription-Token": key, "Accept": "application/json"},
    )
    d = json.loads(urllib.request.urlopen(req, timeout=10).read())
    results = d.get("web", {}).get("results", [])
    print(f"Brave OK: {len(results)} results")
    for r in results[:2]:
        print(f"  - {r.get('title','')}")
except Exception as e:
    print(f"Brave FAIL: {type(e).__name__}: {e}")
