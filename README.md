# EVANGELION — "Neon Overdrive": music video

A generative, code-rendered music video for ["Neon Overdrive"](https://pixabay.com/music/synthwave-neon-overdrive-cyberpunk-gaming-edm-415723/) (mroneilovealot), styled as the NERV HQ command terminal from Evangelion: 16 plates, one HUD instrument per section, every instrument a real sound visualizer (waveform scopes, spectrum analysers, beat-grid countdowns, clap alarms). Every frame is a deterministic function of song time, so the browser preview and the offline 1080p60 / 4K60 export are identical. Built on Giacomo Magnanini's engine from the [P(doom) video](https://github.com/mexicat/pdoom-video), by way of the Lithium video.

Concept, style bible and plate briefs: [`docs/TREATMENT.md`](docs/TREATMENT.md). Engine and scene API: [`docs/ENGINE.md`](docs/ENGINE.md). The shared NERV UI kit: `app/src/scenes/_eva.ts`.

## Audio

The song is not in this repo. Download "Neon Overdrive" by mroneilovealot for free from [Pixabay](https://pixabay.com/music/synthwave-neon-overdrive-cyberpunk-gaming-edm-415723/). Its license covers using it in videos but not re-hosting the file. The analysis data is included (`data/audio.json` has beats, sections, onsets and envelopes; `data/spectrum.bin` has mel and chroma frames). The raw waveform `data/wave.bin` is not included, because it is a playable copy of the track. `analyze.py` rebuilds it, and the scopes stay flat until you do.

Save the track as `audio/evangelion.m4a` (preview) and `audio/evangelion.wav` (analysis and export audio), then rebuild the analysis:

```sh
mkdir -p audio
ffmpeg -i <song.mp3> -vn -c:a aac -b:a 256k audio/evangelion.m4a
ffmpeg -i audio/evangelion.m4a -ac 2 -ar 44100 audio/evangelion.wav
cd analysis
uv run python -m demucs -n htdemucs -o stems ../audio/evangelion.wav
uv run python analyze.py          # data/audio.json, spectrum.bin, wave.bin  (--bars prints the bar table)
```

## Preview

```sh
cd app
bun install
bunx vite --port 5191             # http://localhost:5191, ?t=68 starts at 68 s
```

Keys: space play/pause, ←/→ ±1 s (shift ±5 s), `,`/`.` frame step, `[`/`]` previous/next plate, `l` loop plate, `h` hide UI.

## Render

```sh
cd app
bun scripts/render.ts video --url http://localhost:5191 --samples auto --shutter 0.2 --out ../out/evangelion.mp4
bun scripts/render.ts video --url http://localhost:5191 --scale 2 --samples auto --shutter 0.2 --out ../out/evangelion-4k.mp4
```

## License

Code: MIT (see [LICENSE](LICENSE)). This is a copy of Giacomo Magnanini's [pdoom-video](https://github.com/mexicat/pdoom-video) engine, adapted by Luis Bizarro with a few prompts to Claude.

Fonts are under the SIL Open Font License 1.1 (Archivo, Cormorant Garamond, IBM Plex Mono, EMS stroke fonts). The Hershey stroke fonts carry their own license, which is embedded in each SVG. Each font keeps its license text in its own metadata.

The music is not included and not covered by this license. It is under the Pixabay Content License. Evangelion and NERV are trademarks of their owners. This is a fan-made homage that borrows the genre's UI language, not its logos or footage.
