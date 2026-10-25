# kids-en — curated kids / education playlist for TV Hub

English kids and educational channels for the TCL BeyondTV2, so the kids stay inside TV Hub
instead of YouTube. Built from [iptv-org](https://github.com/iptv-org/iptv); every stream is
probed from this machine before it lands in a playlist.

## Files

| File | What it is |
| :- | :- |
| `curated.tsv` | The review list: iptv-org channel id, tier (`core` / `grey`), group. Hand-edited, the only place channels are chosen. |
| `kids-en.m3u` | `core` tier, 11 channels tuned for a five-year-old, in five groups: `Edukasi` (PBS Kids, ABC Kids, Super Simple Songs, Da Vinci Asia), `Keluarga` (ZooMoo, WildEarth — watched with a parent), `Mandarin` (CCTV-14), `Ngaji` (Masjid al-Haram, with Masjid an-Nabawi as the fallback) and `Hiburan` (Nick Jr. and Nickelodeon on Pluto TV). Deliberately short — fewer channels to scroll through is the point. This is the one to load on the TV. |
| `kids-en-grey.m3u` | `grey` tier: pay-TV channels (Cartoon Network, Nickelodeon, Disney Junior …) restreamed by third parties. Working, but almost certainly unlicensed. Not loaded by default. Generated, and gitignored rather than committed. |
| `candidates.txt` | Live English kids/education channels `curated.tsv` does not mention yet. Review by hand, then add. Generated, and gitignored rather than committed. |

## Rebuild

```
python3 build-kids-playlist.py
```

Needs `curl` and network access, takes a couple of minutes (it opens every stream and, for master
playlists, one variant). Dropped automatically: dead URLs, DRM, geo-blocked, non-HLS, DASH, RTSP
and UDP — TV Hub plays none of those. Re-run when channels start failing on the TV.

## Groups

`Edukasi`, `Keluarga`, `Mandarin`, `Ngaji`, `Hiburan`, plus `Anak` in the grey tier. They show up
as categories in TV Hub.

Movies and live sport are left out on purpose. Free movie channels run one schedule for every age
and drift between ratings as the day goes on, so there is no hour that is reliably safe. Free live
football and basketball exists only as unlicensed restreams, and those carry gambling adverts
almost without exception. Watch both together in a licensed app instead.
