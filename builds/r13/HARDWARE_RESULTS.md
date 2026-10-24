# r13 hardware results

Tested on October 23, 2026 on the author's MV-8800 (OS 1.01, CF card in place of the hard drive), back to back with r12_clean.

| | |
| --- | --- |
| File | `MV8800_r13.PRG` |
| SHA-256 | `3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7` |

## Timing

Stopwatch, test project *InitProj 060*, three saves under the same name:

| Build | Load | Save 1 | Save 2 | Save 3 | Mean save |
| --- | --- | --- | --- | --- | --- |
| r12_clean | 15 s | 15 s | 13.5 s | 13.5 s | about 14 s |
| r13 | 15 s | 14 s | 12 s | 11.5 s | about 12.5 s |

About 1.5 s faster per save, load unchanged. These are three hand-timed saves per build on one project.

## Same-name save integrity

After three r13 same-name saves, all 505 files of *InitProj 060* were byte-identical to the reference checksums in [`reference/InitProj060_reference.json`](../../reference/InitProj060_reference.json).

## Save-as comparison

The project was loaded and Song 1 tempo set to 110 BPM on each build, then saved under a new name:

- `TA` saved with r12_clean
- `TB` saved with r13

Both contain 505 files, with no missing or extra files. 504 are byte-identical, including both `SONG01.MV0/SEQUENCE.MV0` files with the tempo change. Only `PROJECT_.MV0` differs:

| Offset | TA (r12_clean) | TB (r13) | Meaning |
| --- | --- | --- | --- |
| `0x1D` | name letter A | name letter B | project name, expected |
| `0x28` to `0x2A` | `00 A1 84` | `FF 5E 7A` | runtime status field, see below |

### The `0x28` to `0x2A` field

These bytes belong to the 32-bit value at offset +36 of the project header object. Its constructor at `0x8C5CB4C0` sets it to the result of `0x8C67CA60` minus the result of `0x8C67CA40`; both query the system service object at `0x8DB3CDA4` through `0x8C67B530` (selector 1 and selector 0). So it is a status snapshot taken when the save starts, not project data.

Supporting observations:

- other projects on the card hold unrelated values in this field, one of them 0
- a project saved earlier on another r12-based build has the same `00 A1 84` as TA
- TB's value equals the value already stored in the original *InitProj 060*
- the r13 guard does not touch this code path

A repeat r13 save-as to confirm run-to-run behaviour has not been done.

## File system check

Read-only `chkdsk` after the tests: "Windows has scanned the file system and found no problems." 271 folders, 6,473 files.

## Power-loss trade-off

Qualifying writes can stay dirty in RAM longer than with r12_clean because the preliminary flush is skipped. A power cut during a save can lose pending file data or folder-entry updates. No power-loss test was done.
