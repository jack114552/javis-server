import urllib.request, re, os, sys
os.chdir("/opt/javis/server")

# Bing HTML 搜索
url = "https://cn.bing.com/search?q=test&count=3"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})
try:
    html = urllib.request.urlopen(req, timeout=10).read()
    print("Bing page: " + str(len(html)) + " bytes", flush=True)
    
    text = html.decode("utf-8", "ignore")
    matches = re.findall(
        r'<li class="b_algo".*?<h2>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        text, re.DOTALL
    )
    print("Bing results: " + str(len(matches)), flush=True)
    for i, m in enumerate(matches[:3]):
        print("  [" + str(i) + "] " + m[1][:80], flush=True)
except Exception as e:
    print("Bing FAIL: " + str(type(e).__name__) + ": " + str(e), flush=True)
