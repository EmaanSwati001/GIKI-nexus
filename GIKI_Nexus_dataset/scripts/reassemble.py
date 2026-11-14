"""Rebuild the scraped GIKI blob from browser-transfer chunk files."""
import json, sys, re
D = "/tmp/claude-tool-results/3e81f1a9-4a42-550c-9384-dd422da46fed/"
files = ["mcp-remote-devices-Claude_Browser__javascript_tool-1794328665447-e5e484b5.txt",
         "mcp-remote-devices-Claude_Browser__javascript_tool-1794328666996-d7357d29.txt",
         "mcp-remote-devices-Claude_Browser__javascript_tool-1794328668715-ded4ac63.txt",
         "mcp-remote-devices-Claude_Browser__javascript_tool-1794328670332-783d8db5.txt"]
def payload(f):
    t = json.load(open(D + f))[0]["text"]
    t = t.split("\n\n(captured at origin")[0]
    return json.loads(t)
first = payload(files[0]); total = first["len"]
parts = [first["first"]]
for i, f in enumerate(files[1:], 1):
    s = payload(f); tag = f"__CHUNK{i}__"; assert s.startswith(tag); parts.append(s[len(tag):])
blob = "".join(parts)
# JS counts UTF-16 code units; rejoin any surrogate pairs split across chunks.
u16 = blob.encode("utf-16-le", "surrogatepass")
assert len(u16) // 2 == total, (len(u16) // 2, total)
blob = u16.decode("utf-16-le")
data = json.loads(blob)
json.dump(data, open("raw/giki_scrape_raw.json", "w"), ensure_ascii=False, indent=1)
print("ok", total, "profiles", len(data["profiles"]), "listings", len(data["listings"]), data["scraped_at"])
