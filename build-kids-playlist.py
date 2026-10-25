#!/usr/bin/env python3
"""Build kids-en.m3u (and kids-en-grey.m3u) from iptv-org, for TV Hub.

Takes the iptv-org API, keeps the channels listed in curated.tsv, probes every stream from
this network, and writes one entry per channel using its best working stream. Streams that are
dead, DRM-protected, geo-blocked, or not HLS over http(s) are dropped; TV Hub plays none of those.

    python3 kids-tv/build-kids-playlist.py [--out-dir kids-tv] [--jobs 24]

Also writes candidates.txt: live English kids/education channels that curated.tsv does not
mention yet, so the list can be reviewed and extended by hand.
"""
import argparse, collections, concurrent.futures as cf, json, os, re, subprocess, sys, urllib.parse, urllib.request

API = "https://iptv-org.github.io/api"
UA = "Mozilla/5.0 (Linux; Android 11) ExoPlayer"
HERE = os.path.dirname(os.path.abspath(__file__))


def api(name):
    with urllib.request.urlopen(f"{API}/{name}.json", timeout=60) as r:
        return json.load(r)


def curated(path):
    rows = {}
    for line in open(path):
        line = line.split("#")[0].strip()
        if not line:
            continue
        cid, tier, group = line.split("\t")
        rows[cid] = (tier, group)
    return rows


def fetch(url, ua, ref, timeout=12):
    cmd = ["curl", "-sSL", "--max-time", str(timeout), "--max-filesize", "2000000",
           "-A", ua or UA, "-w", "\n@@%{http_code}@@%{url_effective}"]
    if ref:
        cmd += ["-e", ref]
    try:
        r = subprocess.run(cmd + [url], capture_output=True, timeout=timeout + 5)
    except subprocess.TimeoutExpired:
        return None, "timeout", url
    out = r.stdout.decode("utf-8", "replace")
    m = re.search(r"\n@@(\d*)@@(.*)$", out, re.S)
    if not m:
        return None, "no-response", url
    return out[: m.start()], m.group(1), m.group(2).strip()


def probe(s):
    body, code, eff = fetch(s["url"], s["ua"], s["ref"])
    if body is None or code != "200":
        s["status"] = "dead"
        return s
    if "#EXTM3U" not in body:
        s["status"] = "not-m3u"
        return s
    if "EXT-X-SESSION-KEY" in body or "com.widevine" in body or 'URI="skd' in body:
        s["status"] = "drm"
        return s
    if "#EXT-X-STREAM-INF" in body:
        variants = [l.strip() for l in body.splitlines() if l.strip() and not l.startswith("#")]
        if not variants:
            s["status"] = "empty-master"
            return s
        b2, c2, _ = fetch(urllib.parse.urljoin(eff, variants[0]), s["ua"], s["ref"])
        if b2 is None or c2 != "200" or "#EXTINF" not in b2:
            s["status"] = "variant-dead"
            return s
        res = re.findall(r"RESOLUTION=\d+x(\d+)", body)
        s["height"] = max(int(h) for h in res) if res else 0
        s["status"] = "ok"
        return s
    s["status"] = "ok" if "#EXTINF" in body else "no-segments"
    return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default=HERE)
    p.add_argument("--jobs", type=int, default=24)
    a = p.parse_args()

    pick = curated(os.path.join(HERE, "curated.tsv"))
    channels = {c["id"]: c for c in api("channels")}
    feeds = api("feeds")
    logos = api("logos")

    by_channel = collections.defaultdict(list)
    for f in feeds:
        by_channel[f["channel"]].append(f)
    logo = {}
    for l in logos:
        if l["in_use"] and l["channel"] not in logo:
            logo[l["channel"]] = l["url"]

    def english(cid):
        return any("eng" in (f["languages"] or []) for f in by_channel.get(cid, []))

    # Channels worth reviewing: kids or education, English feed, still on air.
    reviewable = {
        c["id"] for c in channels.values()
        if not c["is_nsfw"] and not c["closed"]
        and ({"kids", "education"} & set(c["categories"])) and english(c["id"])
    }

    todo = []
    for s in api("streams"):
        cid = s["channel"]
        if cid not in pick and cid not in reviewable:
            continue
        if "Geo-blocked" in (s["labels"] or []):
            continue
        if not s["url"].startswith(("http://", "https://")):
            continue
        # Discovery only looks at plain HLS; a curated channel is probed whatever its URL looks
        # like, because some give HLS from a redirect with no .m3u8 in the address.
        if cid not in pick and ".m3u8" not in s["url"]:
            continue
        todo.append(dict(channel=cid, url=s["url"], ua=s["user_agent"], ref=s["referrer"],
                         quality=s["quality"], labels=s["labels"] or [], height=0))

    print(f"probing {len(todo)} streams from {len({t['channel'] for t in todo})} channels...", file=sys.stderr)
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        probed = list(ex.map(probe, todo))

    best = {}
    for s in probed:
        if s["status"] != "ok":
            continue
        cur = best.get(s["channel"])
        rank = (s["height"], s["url"].startswith("https://"))
        if cur is None or rank > (cur["height"], cur["url"].startswith("https://")):
            best[s["channel"]] = s

    order = {"Edukasi": 0, "Mandarin": 1, "Ngaji": 2, "Hiburan": 3}
    out = collections.defaultdict(list)
    for cid, (tier, group) in pick.items():
        s = best.get(cid)
        if not s:
            print(f"  no working stream: {cid}", file=sys.stderr)
            continue
        out[tier].append((order.get(group, 9), channels[cid]["name"], cid, group, s))

    for tier, name in (("core", "kids-en.m3u"), ("grey", "kids-en-grey.m3u")):
        path = os.path.join(a.out_dir, name)
        with open(path, "w") as f:
            f.write("#EXTM3U\n")
            for _, cname, cid, group, s in sorted(out[tier]):
                f.write(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{cname}"')
                if cid in logo:
                    f.write(f' tvg-logo="{logo[cid]}"')
                f.write(f' group-title="{group}",{cname}\n')
                if s["ua"]:
                    f.write(f'#EXTVLCOPT:http-user-agent={s["ua"]}\n')
                if s["ref"]:
                    f.write(f'#EXTVLCOPT:http-referrer={s["ref"]}\n')
                f.write(s["url"] + "\n")
        print(f"{path}: {len(out[tier])} channels", file=sys.stderr)

    path = os.path.join(a.out_dir, "candidates.txt")
    with open(path, "w") as f:
        f.write("# Live English kids/education channels not in curated.tsv. Review before adding.\n")
        for cid in sorted(best, key=lambda c: channels[c]["name"].lower()):
            if cid in pick:
                continue
            c = channels[cid]
            f.write(f'{cid}\t{c["country"]}\t{",".join(c["categories"])}\t{c["name"]}\n')
    print(f"{path} written", file=sys.stderr)


if __name__ == "__main__":
    main()
