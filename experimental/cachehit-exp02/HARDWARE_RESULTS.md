# Exp02 final hardware results

These are the firmware owner's final reported MV-8800 hardware results. This documentation update records that report; it does not add testing, independently verify the proposed field interpretation, or modify firmware.

## Firmware identity

The owner tested the build referred to as `MV8800_r12_exp02`. The repository file is `MV8800_r12_cachehit_exp02.PRG`, identified by the same SHA-256:

```text
3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7
```

The firmware PRG, original ZIP, byte-change manifests, and build-verification reports remain unchanged. The ZIP contains the original pre-hardware build notes; this file records the later hardware results.

## Timing

Stopwatch measurements for InitProj 060, using same-name saves:

| Build | Load | Save 1 | Save 2 | Save 3 | Mean save |
| --- | --- | --- | --- | --- | --- |
| r12_clean | 15 s | 15 s | 13.5 s | 13.5 s | about 14 s |
| exp02 | 15 s | 14 s | 12 s | 11.5 s | about 12.5 s |

The reported mean saving is **about 1.5 s per save**, exceeding the owner's 0.5 s threshold. Load time is unchanged. These are three hand-timed saves per build on this test project, rather than a measurement of every project or save workload.

## Same-name save integrity

After three exp02 same-name saves of InitProj 060, **all 505 files were byte-identical to the reference checksums**.

## Save-as comparison with an edited project

The owner loaded InitProj 060 and set Song 1 tempo to 110 BPM for each comparison:

- `TA` was saved using r12_clean.
- `TB` was saved using exp02.

Each project contained 505 files, with no missing or extra files. **504 files were byte-identical**, including the two `SONG01/SEQUENCE.MV0` files. Only `PROJECT_.MV0` differed:

| File offset | TA (r12_clean) | TB (exp02) | Observation |
| --- | --- | --- | --- |
| `0x1D` | Name letter A | Name letter B | Expected project-name difference |
| `0x28–0x2A` | `00 A1 84` | `FF 5E 7A` | Unresolved field; TB matches the original InitProj 060 value |

### Owner's investigation of the unresolved field

The owner identified the containing field as the 32-bit value at COM object `+36`. In the COM constructor at `0x8C5CB4C0`, it is initialized to the return value of `0x8C67CA60` minus the return value of `0x8C67CA40`. Both query the service object at `0x8DB3CDA4` through `0x8C67B530`, using selector 1 versus 0.

The owner observed unrelated values in other projects, including zero. T1, saved using the r12-based r13-v3 build, has the same `00 A1 84` differing bytes as TA. The exp02 guard does not modify this code path.

A runtime status or memory snapshot is a possible explanation, **not a confirmed interpretation**. The owner did not repeat the exp02 save-as to establish run-to-run consistency. The comparison therefore does not prove that every save-as difference is harmless or independent of the firmware change.

## File-system check

Read-only CHKDSK after the exp02 tests reported:

> Windows has scanned the file system and found no problems.

Reported totals: **271 folders and 6,473 files**.

## Status and power-loss trade-off

The owner closed the task with these results: the measured save improvement exceeds the threshold, same-name checksum comparisons passed, and CHKDSK passed. The save-as field difference remains documented and unresolved. `r12_clean` remains the fallback build.

The owner understands the disclosed power-loss trade-off: qualifying writes can stay dirty in RAM longer than with r12_clean because the preliminary flush is deferred. A power cut can lose pending file data or folder-entry updates that r12_clean might already have written. Existing cache capacity and explicit/final flush code are unchanged; the logical impact of a power cut is not bounded by the cache's byte capacity. No power-loss test was reported.
