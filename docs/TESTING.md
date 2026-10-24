# Testing and verification

Every build was checked on three levels: the file itself, the speed on the hardware, and the data it writes.

## 1. Build checks (before anything goes on the instrument)

- The PRG is exactly 4,194,304 bytes, the header (bytes `0x0` to `0x20043`) is unchanged, the compressed stream ends before `0x3FFFF0`, and the 16-byte trailer (ending `F6 81`) is preserved.
- The compressed stream is decoded again and compared with the intended program image: no change may exist that was not declared.
- Every byte that differs from stock is listed and explained. For r13, all 1,769 r12 bytes were also checked to be untouched.
- New code was tested in an instruction-level emulator before flashing. r13's guard passed 12,193 emulated cases and 18 integration cases that ran the original firmware routines with and without the guard. See [r13 BUILD_NOTES.md](../builds/r13/BUILD_NOTES.md) for the method and its limits.

## 2. Speed

### Stopwatch (hardware)

Test project *InitProj 060*: 505 files, 16 songs, 128 library patches, `SAMPLE__.MV0` of 10,605,670 bytes.

| Build | Load | Save 1 | Save 2 | Save 3 | Mean save |
| --- | --- | --- | --- | --- | --- |
| Stock OS 1.01 | about 20 s | about 35 s | | | about 35 s |
| r12_clean | 15 s | 15 s | 13.5 s | 13.5 s | about 14 s |
| r13 | 15 s | 14 s | 12 s | 11.5 s | about 12.5 s |

The r12_clean and r13 rows were measured back to back on October 23, 2026, with the same project, card and procedure (load once, then three saves under the same name). Stopwatch timing is accurate to about half a second per reading.

### Profiler (development builds)

The r1 to r12 development builds contain a sampling profiler that records the running code address every 2 ms during a load or save and writes the result to the card. This showed where time was spent (card wait, flushes, cache work, CPU work) and confirmed each change. Profiler windows are shorter than stopwatch times because they cover only the file operation itself.

| Build | Load window | Save window | Main change since previous row |
| --- | --- | --- | --- |
| r1 | 13.5 s | 33.5 s | profiler on top of v4 |
| r7 | 13.6 s | 22.2 s | smart write, read skip for overwritten blocks (r2 to r7) |
| r8 | 13.6 s | 13.9 s | one volume flush per project save |
| r10 | 12.9 s | 13.8 s | no wasted zero-filling |
| r11 | 12.8 s | 12.0 s | zero-fill skip for overwritten blocks, sample RAM loop, USB wait |
| r12 | 12.3 s | 13.6 s | final profiler build (save varies by about 1.5 s between runs) |

A matched load and save profile of r12, together with a read-only capture of the card's FAT and directory structures taken straight after, was the basis for the r13 change.

## 3. Data integrity

Speed means nothing if a single byte of a project changes, so every hardware test ends with a file comparison.

**Same-name save.** Load *InitProj 060*, save it under the same name three times, then copy all 505 files from the card and compare them with the reference checksums in [`reference/InitProj060_reference.json`](../reference/InitProj060_reference.json). Every file must match.

**Save-as A/B.** Load the project on build A, change one thing (Song 1 tempo to 110 BPM), save as `TA`. Repeat on build B and save as `TB`. Compare `TA` and `TB` file by file. Only the project name in `PROJECT_.MV0` should differ.

**File system.** After the tests, run a read-only `chkdsk L:` on the card (never `/f`).

The comparisons use [`tools/project_checksums.py`](../tools/README.md).

### Results for r13 against r12_clean

| Check | Result |
| --- | --- |
| Same-name saves, 505 files vs reference | all 505 identical |
| Save-as, TA (r12_clean) vs TB (r13) | 504 of 505 identical, including `SONG01.MV0/SEQUENCE.MV0` with the tempo change |
| `PROJECT_.MV0` | name letter at `0x1D` (expected) and bytes `0x28` to `0x2A` (see below) |
| chkdsk (read-only) | no problems found, 271 folders, 6,473 files |

Bytes `0x28` to `0x2A` of `PROJECT_.MV0` hold a 32-bit value that the OS fills in when a save starts: it asks a system service for two numbers and stores the difference. It is a runtime status value, not project data. Other projects on the card hold unrelated values there (one is 0), and a project saved on another r12-based build has the same value as TA. A repeat r13 save-as to confirm run-to-run behaviour has not been done. Full details: [HARDWARE_RESULTS.md](../builds/r13/HARDWARE_RESULTS.md).

## Reproducing the tests

1. Copy the test project folder from the card to a computer before changing firmware.
2. Install the build and run the same-name and save-as procedures above.
3. Copy the saved folders back and compare:

```text
python tools/project_checksums.py compare "path/to/before/InitProj 060.PRJ" "L:\PROJECTS\InitProj 060.PRJ"
python tools/project_checksums.py compare "L:\PROJECTS\TA          .PRJ" "L:\PROJECTS\TB          .PRJ"
```

MV-8800 pads project folder names with spaces to 12 characters, so `TA` is stored as `TA` followed by 10 spaces.
