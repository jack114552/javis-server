"""测试联网搜索"""
import urllib.request, re, json

# 测试 Bing 搜索
url = "https://cn.bing.com/search?q=今天天气"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})
try:
    html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore")
    print(f"Bing 返回长度: {len(html)}")
    
    # 匹配搜索结果
    matches = re.findall(
        r'<li class="b_algo".*?<h2>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<p[^>]*>(.*?)</p>',
        html, re.DOTALL
    )
    print(f"Bing 解析到 {len(matches)} 条结果")
    for i, m in enumerate(matches[:3]):
        print(f"  [{i}] {re.sub(r'<[^>]+>','',m[1]).strip()[:60]}")
        print(f"       {m[0][:60]}")
except Exception as e:
    print(f"Bing 失败: {e}")

# 测试 Brave Search（有 key）
try:
    req2 = urllib.request.Request(
        "https://api.search.brave.com/res/v1/web/search?q=今天天气&count=3",
        headers={"X-Subscription-Token": "sk-8c3…c450", "Accept": "application/json"},
    )
    data = json.loads(urllib.request.urlopen(req2, timeout=8).read())
    results = data.get("web", {}).get("results", [])
    print(f"\nBrave 返回 {len(results)} 条结果")
    for r in results[:2]:
        print(f"  {r.get('title','')[:60]}")
except Exception as e:
    print(f"Brave 失败: {e}")
