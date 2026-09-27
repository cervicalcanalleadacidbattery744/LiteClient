# EVANGELION — "Neon Overdrive": treatment

A generative, code-rendered music video for "Neon Overdrive" (mroneilovealot, cyberpunk gaming EDM, 133.33 BPM, 184.4 s, instrumental with a few vocal chops). Same engine and premise as the Lithium video: every frame is a deterministic function of song time, driven by the analysis in `data/audio.json` (beat grid, sections, kick/clap/hat/vocal onsets, stem envelopes, bass pitch, mel spectrogram, chroma, raw waveform).

## Concept: NERV HQ, one instrument per section

The video is the command terminal of NERV headquarters during an Angel attack, shown one screen at a time. Every plate is a **different instrument of the Evangelion HUD**, and every instrument is a real **sound visualizer**: the scopes trace the real waveform, the analysers show the real spectrum, the countdowns are the bar grid, the alarms are the claps. The arc: boot → routine monitoring (grooves) → first contact (build 1) → A.T. FIELD (drop 1) → pattern blue (drop 1b) → sortie (break 2 / drop 2) → the city holds its breath (breakdown) → sync overflow (build 2) → BERSERK (drop 3) → third impact (drop 3b) → END.

## Style bible (match the Evangelion HUD / NERV UI exactly)

- **Ground:** pure terminal black (`ink`, #050403). Screens, not scenes: flat, graphic, dense, precise. Full-bleed plates.
- **Colour:** **command orange** (`orange` #FF7A00) is the primary HUD colour for lines, text, frames and data; `amber` (#FFB000) for highlights. **EMERGENCY red** (`red` #FF1A1A, panels in `blood`) for alerts, warnings and hits. Instrument accents: **phosphor green** (`green` #39FF6A) for scopes, MAGI "approve" and psychographs; **pattern blue** (`cyan` #00C8FF) for targets, the Angel and "BLOOD TYPE: BLUE"; **Unit-01 purple + lime** (`purple`, `lime`) only for sync/berserk. Warm white (`bone`) sparingly for the biggest type. GLSL: `C_ORANGE, C_AMBER, C_RED, C_GREEN, C_CYAN, C_PURPLE, C_LIME, C_INK, C_BONE`. Canvas: `rgba('orange', a)`.
- **Shapes:** chamfered (45°-cut) panels with a solid header tab and the title knocked out in black (`panel`), corner brackets (`brackets`), **hexagons and hex grids** everywhere (`hexPath`, `hexGrid`, `GLSL_EVA`), diagonal **hazard stripes** (`hazard`), thin rules, tick scales, crosshairs, concentric range rings, octagons.
- **Type:** three voices.
  1. **Title card:** heavy **condensed serif**, white or orange, huge, stacked in wildly different sizes, hard-aligned (`evaTitle`, `condensed` — Cormorant squeezed to ~60 % width). Used for plate titles ("EMERGENCY", "A.T. FIELD", "BERSERK").
  2. **Data:** IBM Plex Mono, tracked caps labels, live values (`evaLabel`, `F.mono`).
  3. **Japanese:** every major label is bilingual: English mono caps + a Japanese line (`jp()` / `JP_SANS`, `JP_SERIF`): 警告 (warning), 緊急 (emergency), 使徒 (Angel), 活動限界 (activity limit), 内部電源 (internal power), 外部電源 (external power), 同調率 (sync ratio), 暴走 (berserk), 承認 (approve), 否決 (reject), 解析中 (analysing), 目標 (target), 第3新東京市 (Tokyo-3), 神経接続 (neural connection), 心理グラフ (psychograph).
- **Instruments:** 7-segment countdown digits (`sevenSeg`), segmented level meters (`segMeter`), scrolling tickers (`ticker`), hex data filler (`hexData`), warning boxes (`warningBox`).
- **Texture:** CRT scanlines + phosphor mask over every plate (`makeScanPass`, draw it last), light bloom on the brightest orange, occasional hard glitch (row offsets, RGB split via `ca`) on hits. No soft gradients-as-decoration, no generic "sci-fi" blue; it must read as NERV.
- **Do not** use the NERV logo, SEELE logo or Evangelion wordmark literally. Everything else (colours, layouts, hexes, bilingual captions, condensed serif cards, MAGI names, "PATTERN BLUE", "SOUND ONLY") is the genre and is encouraged.

## Motion language (133.33 BPM, beat 0.45 s, bar 1.8 s)

- **Kick:** the bounce (`duck(f, au)`): meters jump, panels nudge, brightness dips and springs back.
- **Clap (2 and 4):** alarms: red flashes, warning boxes blink, hazard stripes step, a panel inverts.
- **Hats:** tick marks, data rows scroll one line, hex cells flicker.
- **Bass (`f.a.bass`, `audio.bassMidi`):** mass: gauge needles, field strength, the size of the rings.
- **Vocal chops:** the Angel speaks: glyph bursts, cyan targets appear.
- **Builds:** countdowns, grids tighten, sync ratio climbs, everything accelerates; the last beat before a drop freezes or goes black. **Drop downbeats are hard cuts with impact** (post `flash`, `zoom`, `shake`).
- **Breaks:** drums out, the screen stops pumping; slow scans, data settles.

## Song map (bar k = `barTime(au, k)`; bar 0 = 4.82 s)

| plate | window (s) | bars | music |
|---|---|---|---|
| boot | 0 – 8.42 | –2..2 | intro, pads only |
| magi | 8.42 – 17.42 | 2–7 | groove 1: drums + bass enter on the downbeat |
| psycho | 17.42 – 28.22 | 7–13 | groove 1 cont.; bar 12 (26.42) one-bar break (pad swell) |
| radar | 28.22 – 37.22 | 13–18 | groove 2 |
| harmonics | 37.22 – 48.02 | 18–24 | groove 2 cont.; bar 23 (46.22) pad-swell fill |
| seele | 48.02 – 57.02 | 24–29 | break 1: bass + pads, no drums |
| battery | 57.02 – 67.82 | 29–35 | build 1: drums back, vocal chops bars 31–33, bar 34 fill |
| atfield | 67.82 – 85.82 | 35–45 | DROP 1 |
| alert | 85.82 – 102.02 | 45–54 | drop 1b (bar 45 highest energy) |
| plug | 102.02 – 112.82 | 54–60 | break 2 (bars 54–55 pads only) → drop 2 at bar 56 (105.62) |
| target | 112.82 – 121.82 | 60–65 | drop 2 cont. (drums + bass, no pads) |
| city | 121.82 – 134.42 | 65–72 | breakdown: pads only, vocal chop bar 71 |
| sync | 134.42 – 145.22 | 72–78 | build 2: chops bars 74–75, bar 76 dropout, bar 77 roll |
| berserk | 145.22 – 161.42 | 78–87 | DROP 3 (final drop) |
| impact | 161.42 – 177.62 | 87–96 | drop 3b |
| end | 177.62 – 184.41 | 96– | outro: pads to silence |

## The plates

### boot — "SYSTEM START"
Black. A terminal boots: lines of mono text type out (NERV OS, MAGI link, neural connection check, hex data), a hex emblem assembles from hex cells on the pad swells, orange rules sweep in. On the last bar the screen clears to a title card in condensed serif: **NEON OVERDRIVE** / episode-card layout with a small "EPISODE:01" and a Japanese subtitle (例: 「ネオン・オーバードライブ」). Cut on the drums.

### magi — "MAGI SYSTEM"
The three MAGI supercomputers as the classic diagram: three chamfered blocks **MELCHIOR·1, BALTHASAR·2, CASPER·3** arranged in a triangle joined by thick lines, a central "MAGI" label, each block a live processor: the low / mid / high bands fill it (hex cells or scan bars). Each kick casts a vote: blocks flash 承認 (green, APPROVE) or 否決 (red, REJECT) on alternating patterns; a vote tally and "DELIBERATION" status. Side panels: code rows scrolling on hats.

### psycho — "PSYCHOGRAPH"
Green-phosphor multi-channel monitor: 4–6 stacked scope channels (the real waveform, bass stem, highs, kick envelope) with persistence, labelled pilot channels (PILOT 01/02/03), graticule, a "心理グラフ" header and readouts. The one-bar break (bar 12) makes the traces flatline and pulse, then the groove snaps back.

### radar — "TACTICAL"
Top-down tactical radar: concentric range rings, rotating sweep synced to the bar (one turn per bar), bearing scale, the Angel as a cyan contact approaching (blood type blue), UN forces as orange blips that light when the sweep passes; blip sizes from spectrum bands, kicks pulse the rings. Range readout, heading, "使徒接近" label.

### harmonics — "HARMONICS"
The Eva harmonics / waveform analyser: a big segmented bar spectrum (the real mel spectrum, orange blocks, red peaks) inside a hex-framed panel, with a mirrored waveform strip, peak-hold ticks, band labels in Hz, a "HARMONICS NORMAL" status that flips to amber on the bar-23 fill.

### seele — "SOUND ONLY"
Break 1. Black. A ring or row of tall black monoliths floating in darkness, each with a red number (01–12) and "SOUND ONLY"; each monolith is a chroma bin of the harmonic stem: its red text and edge glow brighten with that pitch class. Slow drift; the bass makes the one speaking glow. Ominous, spacious, no pump.

### battery — "INTERNAL BATTERY"
Build 1. The famous activity-limit countdown: huge 7-segment digits counting down (the remaining build time, e.g. 05:00:00 → 00:00:00, accelerating), "活動限界まで" label, INTERNAL / EXTERNAL power indicators (external cable disconnected on the downbeat: 外部電源 切断), battery bars draining; the vocal chops (bars 31–33) spike warnings; bar 34 fill: digits flash red, freeze at 00:00:00 → hard cut to black-orange flash into the drop.

### atfield — "A.T. FIELD"
Drop 1. The Absolute Terror field: a full-screen shader of glowing orange hexagonal shield planes (octagonal rings of hex cells) that ripple outward on every kick, bass displaces them, claps shatter a ring of cells, hats sparkle cells. Overlay: "A.T. FIELD" condensed card, field strength meter, "位相空間 展開" label. Maximum impact, bloom.

### alert — "PATTERN BLUE"
Drop 1b. Full alarm: red hazard bands scrolling, the big "EMERGENCY / 緊急事態" warning box, "PATTERN BLUE" in cyan, a grid of alert panels flashing on claps, scrolling tickers, the Angel's analysis panel ("BLOOD TYPE: BLUE", "解析中"). Every clap inverts a panel red; kicks shake.

### plug — "ENTRY PLUG"
Break 2 → drop 2. Entry plug insertion: a first-person tunnel of rings / hex frames receding (LCL orange-amber), depth gauge and "LCL 注水" readouts during the 2 break bars (slow insertion), then on the drop the plug locks ("神経接続 開始") and the tunnel races with the kicks, synchronisation stages listed and ticked off (A10 nerve connection, pulse, harmonics: all green).

### target — "POSITRON RIFLE"
Drop 2 cont. Targeting scope: a big reticle with range rings and cross hairs tracking a cyan target (drifting with the bass), zoom brackets snapping on kicks, charge meter filling on the bar (positron rifle charge), "FIRE" on every 2-bar phrase with a white flash along the aim line; elevation/azimuth scales, wind/gravity/geomagnetic correction readouts.

### city — "TOKYO-3"
Breakdown, pads only. A night wireframe of Tokyo-3 (orange hairline buildings on a grid, camera slowly orbiting, perspective): building heights breathe with the mel bands (towers rising from the geofront like the city's retractable buildings), a scanning line sweeping the city, district labels (第3新東京市). Calm, spacious, no pump. The vocal chop at bar 71 lights a cyan beacon.

### sync — "SYNCHRONIZATION"
Build 2. The sync-ratio test: huge percentage in condensed serif climbing from 41.3 % to 400 % as the build rises (accelerating), a sync graph, two heartbeat traces converging, Unit-01 palette creeping in (purple frames, lime numbers); bar 76 dropout: everything freezes, "同調率 400%" … bar 77 roll: readouts glitch, → hard cut.

### berserk — "BERSERK"
Drop 3. The Unit-01 berserker: purple/lime and red glitching HUD: "暴走" giant kanji, BERSERK condensed card, a heart monitor tracing the kick, limiter bars all maxed, red-purple hex fields exploding on kicks, row-glitch on claps, "ACTIVITY LIMIT EXCEEDED" tickers. The most violent plate, still composed.

### impact — "THIRD IMPACT"
Drop 3b. The NERV control wall: a 3×3 (or asymmetric) grid of mini instruments all running at once (scope, spectrum, 7-seg counter, radar, hex field, warning box, sync %), cycling on each 2-bar phrase, everything red-shifting towards the end; a giant cross of light / red horizon grows behind. Bar 95 last bar: panels fail one by one to black.

### end — "END"
Outro, pads to silence. Black. A condensed-serif end card: **終劇** / "NEON OVERDRIVE" / credits (music: mroneilovealot), a slow flatline psychograph, the last numbers settling to zero, fade to black at the end.
