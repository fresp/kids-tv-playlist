# kids-en — curated kids / education playlist for TV Hub

English kids and educational channels for the TCL BeyondTV2, so the kids stay inside TV Hub
instead of YouTube. Built from [iptv-org](https://github.com/iptv-org/iptv); every stream is
probed from this machine before it lands in a playlist.

## Files

| File | What it is |
| :- | :- |
| `curated.tsv` | The review list: iptv-org channel id, tier (`core` / `grey`), group. Hand-edited, the only place channels are chosen. |
| `kids-en.m3u` | `core` tier, 11 channels: public broadcasters (PBS Kids, ABC Kids, TVOKids), official FAST channels (Nickelodeon and Nick Jr. on Pluto TV, Retro Kid, Lego, Super Simple Songs) and free-to-air (ZooMoo, WildEarth). Deliberately short — fewer channels to scroll through is the point. This is the one to load on the TV. |
| `kids-en-grey.m3u` | `grey` tier: pay-TV channels (Cartoon Network, Nickelodeon, Disney Junior, BabyTV …) restreamed by third parties. Working, but almost certainly unlicensed. Not loaded by default. |
| `candidates.txt` | Live English kids/education channels `curated.tsv` does not mention yet. Review by hand, then add. |

## Rebuild

```
python3 build-kids-playlist.py
```

Needs `curl` and network access, takes a couple of minutes (it opens every stream and, for master
playlists, one variant). Dropped automatically: dead URLs, DRM, geo-blocked, non-HLS, DASH, RTSP
and UDP — TV Hub plays none of those. Re-run when channels start failing on the TV.

## Groups

`Balita` (toddler), `Anak` (6–10), `Edukasi`. They show up as categories in TV Hub.
