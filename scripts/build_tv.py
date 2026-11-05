"""Build data/tv.json: live sports broadcasts on Middle East channels.

Source: free XMLTV guides published by epgshare01.online (beIN MENA, Alkass,
UAE/Saudi/Kuwait sports channels). Runs in GitHub Actions; the app reads the
JSON from the same site, so no browser cross-site requests are needed.
"""
import gzip, io, json, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

FILES = ["epg_ripper_BEIN1.xml.gz", "epg_ripper_AE1.xml.gz", "epg_ripper_SA1.xml.gz", "epg_ripper_EG1.xml.gz"]
BASE = "https://epgshare01.online/epgshare01/"
SPORT_CH = re.compile(r"(?i)bein|alkass|ktv\.?sport|kuwait\.?sport|ad\.?sports|abu\.?dhabi\.?sports|dubai\.?sports|sharjah\.?sport|ksa\.?sports|ssc|thmanyah|on\.?time\.?sport|oman\.?tv\.?sport|starzplay\.?sports")
SKIP_CH = re.compile(r"(?i)news|4k|radio|fm\b")
VERSUS = re.compile(r"(?i)\s(?:vs?\.?|×|x)\s|\s-\s")
REPLAY = re.compile(r"(?i)\b(replay|highlights|re-?run|classic|magazine|preview|review|studio|pre-?match|post-?match)\b|إعادة|ملخص")

def pretty(cid, disp):
    n = (disp or "").strip()
    m = re.match(r"(?i)beIN_SPORTS_?(MAX|XTRA)?_?(?:Digital_)?0?(\d+)", cid)
    if cid.endswith(".bein"):
        if cid.lower().startswith("alkass_"):
            return "Alkass " + cid.split("_")[1]
        if m:
            kind = (m.group(1) or "").upper()
            return "beIN SPORTS " + ({"MAX": "MAX ", "XTRA": "XTRA "}.get(kind, "")) + m.group(2)
        m2 = re.search(r"(?i)beINSPORTS(XTRA)?(\d+)", cid)
        if m2: return "beIN SPORTS " + ("XTRA " if m2.group(1) else "") + m2.group(2)
        if "FTA" in cid: return "beIN SPORTS (free-to-air)"
        if "ENGLISH" in cid or "FRENCH" in cid: return n or cid
    n = re.sub(r"\.(ae|sa|eg|bein)$", "", n or cid)
    n = re.sub(r"^(en|ar):\.", "", n).replace(".", " ")
    n = re.sub(r"(?i)\s+HD[R]?$", "", n).strip()
    return n

def ts(v):
    return int(datetime.strptime(v.strip(), "%Y%m%d%H%M%S %z").timestamp())

def main():
    now = time.time(); lo, hi = now - 36 * 3600, now + 4 * 86400
    out, names = {}, {}
    for f in FILES:
        try:
            raw = urllib.request.urlopen(urllib.request.Request(BASE + f, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read()
            root = ET.parse(io.BytesIO(gzip.decompress(raw))).getroot()
        except Exception as e:
            print("skip", f, e, file=sys.stderr); continue
        for ch in root.iter("channel"):
            cid = ch.get("id", "")
            if not SPORT_CH.search(cid) or SKIP_CH.search(cid): continue
            dn = ch.findtext("display-name") or ""
            names[cid] = pretty(cid, dn)
        for p in root.iter("programme"):
            cid = p.get("channel", "")
            if cid not in names: continue
            title = (p.findtext("title") or "").strip()
            if not title or not VERSUS.search(title) or REPLAY.search(title): continue
            try: s, e = ts(p.get("start")), ts(p.get("stop"))
            except Exception: continue
            if e < lo or s > hi or e - s < 40 * 60: continue
            key = (names[cid], s)
            out[key] = {"c": names[cid], "s": s, "e": e, "t": title[:140]}
    items = sorted(out.values(), key=lambda x: (x["s"], x["c"]))
    json.dump({"updated": int(now), "items": items}, open("data/tv.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(len(items), "programmes;", "channels:", sorted(set(names.values())))

if __name__ == "__main__":
    main()
