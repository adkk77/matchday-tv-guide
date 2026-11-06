#!/usr/bin/env python3
"""Build data/fpl.json: Fantasy Premier League points for every player.

The FPL API blocks browsers (no CORS), so this runs in a GitHub Action and the
app reads the small JSON file it writes.
"""
import json, os, urllib.request, datetime

BASE = "https://fantasy.premierleague.com/api/"
HDR = {"User-Agent": "Mozilla/5.0 (matchday-tv-guide FPL builder)"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HDR)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

def main():
    bs = get("bootstrap-static/")
    events = bs.get("events", [])
    cur = next((e for e in events if e.get("is_current")), None) or next((e for e in events if e.get("is_next")), None)
    gw = cur["id"] if cur else None
    teams = {t["id"]: t["name"] for t in bs["teams"]}
    pos = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD", 5: "MGR"}
    live = {}
    if gw:
        try:
            for el in get(f"event/{gw}/live/").get("elements", []):
                bd = []
                for fx in el.get("explain", []):
                    for s in fx.get("stats", []):
                        if s.get("points") or s.get("identifier") == "minutes":
                            bd.append([s["identifier"], s.get("value", 0), s.get("points", 0)])
                live[el["id"]] = {"pts": el["stats"].get("total_points", 0), "bps": el["stats"].get("bps", 0),
                                  "bonus": el["stats"].get("bonus", 0), "min": el["stats"].get("minutes", 0), "bd": bd}
        except Exception as e:  # keep season data even if live fails
            print("live failed:", e)
    players = []
    for p in bs["elements"]:
        L = live.get(p["id"], {})
        players.append({
            "id": p["id"], "web": p["web_name"], "first": p["first_name"], "last": p["second_name"],
            "team": teams.get(p["team"], ""), "pos": pos.get(p["element_type"], ""),
            "total": p.get("total_points", 0), "gw": L.get("pts", p.get("event_points", 0)),
            "bps": L.get("bps", 0), "bonus": L.get("bonus", 0), "min": L.get("min", 0), "bd": L.get("bd", []),
            "cost": p.get("now_cost", 0) / 10, "sel": p.get("selected_by_percent", ""), "form": p.get("form", ""),
            "ppg": p.get("points_per_game", ""), "goals": p.get("goals_scored", 0), "assists": p.get("assists", 0),
            "cs": p.get("clean_sheets", 0), "bonusTotal": p.get("bonus", 0), "code": p.get("code"),
        })
    out = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "gw": gw, "gwName": cur["name"] if cur else "", "gwFinished": bool(cur and cur.get("finished")),
           "teams": sorted(teams.values()), "players": players}
    os.makedirs("data", exist_ok=True)
    old = None
    try:
        old = json.load(open("data/fpl.json"))
    except Exception:
        pass
    if old and {k: v for k, v in old.items() if k != "updated"} == {k: v for k, v in out.items() if k != "updated"}:
        print("no change"); return
    json.dump(out, open("data/fpl.json", "w"), separators=(",", ":"), ensure_ascii=False)
    print("wrote", len(players), "players, GW", gw)

if __name__ == "__main__":
    main()
