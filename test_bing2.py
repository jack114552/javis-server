import urllib.request, re, json, os
os.chdir("/opt/javis/server")

query = "test"
url = "https://cn.bing.com/search?q=" + query
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})
html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore")

# 简单提取：找 b_algo 后面跟的 h2 > a
results = []
for block in html.split('<li class="b_algo"')[1:]:
    try:
        # 提取 href
        href_start = block.find('href="')
        if href_start == -1: continue
        href_start += 6
        href_end = block.find('"', href_start)
        url = block[href_start:href_end]
        
        # 提取 title (在 > 和 </a> 之间)
        a_end = block.find("</a>")
        if a_end == -1: continue
        # 找到 h2 后面的第一个 >
        h2_end = block.find(">")
        if h2_end == -1: continue
        title_section = block[h2_end+1:a_end]
        title = re.sub(r'<[^>]+>', '', title_section).strip()
        
        if title and url:
            results.append({"title": title[:200], "url": url})
    except:
        pass

print(json.dumps({"success": True, "results": results[:5], "count": len(results[:5])}, ensure_ascii=False))
