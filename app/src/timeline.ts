// The edit: which plate plays when. Boundaries come from the analysed sections (data/audio.json,
// 8-bar phrases on the downbeat grid); the 16-bar drops are split in two plates on their 8th bar.
import type { TimelineEntry } from './engine/engine';
import type { SceneClass } from './engine/scene';
import type { Lyrics } from './engine/lyrics';
import type { AudioData } from './engine/audio';

// Scene modules are discovered lazily so a missing/broken scene never breaks the build.
const modules = import.meta.glob<{ default: SceneClass }>('./scenes/*.ts');
const scene = (name: string) => () => {
  const m = modules[`./scenes/${name}.ts`];
  return m ? m() : Promise.reject(new Error(`scene module not found: scenes/${name}.ts`));
};

export function makeTimeline(_ly: Lyrics, au: AudioData): TimelineEntry[] {
  // bar k = the k-th bar of the song's phrase grid (bar 0 at 4.82 s; 133.33 BPM, 1.8 s per bar).
  // au.downbeats starts two bars earlier (bar -2 at 1.22 s).
  const bar = (k: number) => au.downbeats[k + 2] ?? au.downbeats[au.downbeats.length - 1]! + (k + 2 - au.downbeats.length + 1) * 1.8;
  const E = (id: string, start: number, end: number, extra: Partial<TimelineEntry> = {}): TimelineEntry =>
    ({ id, load: scene(id), start, end, ...extra });

  // 16 plates: a NERV HQ command terminal, one instrument per section (docs/TREATMENT.md)
  return [
    E('boot', 0, bar(2)), //          intro (pads)                   BOOT + title card
    E('magi', bar(2), bar(7)), //     groove 1                       MAGI SYSTEM vote
    E('psycho', bar(7), bar(13)), //  groove 1 end + 1-bar break     PSYCHOGRAPH scopes
    E('radar', bar(13), bar(18)), //  groove 2                       TACTICAL RADAR
    E('harmonics', bar(18), bar(24)), // groove 2 (bar 23 fill)      HARMONICS analyser
    E('seele', bar(24), bar(29)), //  break 1 (bass + pads)          SOUND ONLY monoliths
    E('battery', bar(29), bar(35)), // build 1                       INTERNAL BATTERY countdown
    E('atfield', bar(35), bar(45)), // DROP 1                        A.T. FIELD
    E('alert', bar(45), bar(54)), //  drop 1b                        PATTERN BLUE / EMERGENCY
    E('plug', bar(54), bar(60)), //   break 2 → drop 2               ENTRY PLUG insertion
    E('target', bar(60), bar(65)), // drop 2                         POSITRON RIFLE target lock
    E('city', bar(65), bar(72)), //   breakdown (pads)               TOKYO-3 wireframe
    E('sync', bar(72), bar(78)), //   build 2                        SYNC RATIO → 400 %
    E('berserk', bar(78), bar(87)), // DROP 3                        BERSERK
    E('impact', bar(87), bar(96)), // drop 3b                        THIRD IMPACT control wall
    E('end', bar(96), au.duration), // outro                          END card
  ];
}
