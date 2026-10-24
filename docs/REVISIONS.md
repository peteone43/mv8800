# Revision history: v1 to r13

This is the full development log, revision by revision: what was changed, why, and what it did to load and save time.

## Where it started

On the test project (*InitProj 060*, 505 files), Roland OS 1.01 took about **20 s to load and 35 s to save**, even with a fast CF card in place of the hard drive. The update file was decoded (Roland's LZ98 compression, see [TECHNICAL.md](TECHNICAL.md)) into the 7.2 MB SH-3 program image and analysed in Ghidra. A matching encoder was written so patched images could be packed back into valid update files.

## Before profiling: v1 to v4

| Build | Change |
| --- | --- |
| v1 | One-byte waveform patch at `0x8C4B825F`, carried over from the starting build. |
| v2 | New FAT cluster-chain scan for FAT32 (finds the end of a contiguous cluster run in one pass, and lets seeks skip whole clusters). Built on a side branch and not continued. |
| v3 | **IDE transfers by CPU copy.** The stock driver moves every 512-byte sector with the DMA controller in 64-word chunks while the CPU busy-polls it. v3 copies the data with the CPU directly, with the same bus timing and uncached buffers. |
| v4 | **IDE bus timing.** Bus area 6 wait states 10 to 6, data setup time 3.5 to 2.5 cycles. |

v4 is the base of everything that follows.

## Profiling: r1 to r12

From r1 on, every build carried a **sampling profiler**: a wrapper on the 1 ms timer interrupt records what the CPU is doing every 2 ms (current task, program counter and the call chain found on the stack), stage markers tag which part of a load or save is running, and when the operation finishes the records are written to the card. Each revision was flashed, then the test project was loaded and saved, and the profile showed where the time went.

All r1 to r12 builds were made on October 14, 2026. "Load" and "save" below are the profiler's measurement windows, which are a little shorter than stopwatch times because they cover only the file operation itself.

| Rev | Load | Save | Main change |
| --- | --- | --- | --- |
| r1 | 13.5 s | 33.5 s | profiler, audio mute nesting fix |
| r2 | | | smart write (first version) |
| r3 | 13.5 s | 30.0 s | sector read/write counters |
| r4 | 13.5 s | 28.4 s | smart write rework, IDE read benchmark |
| r5 | 13.5 s | 23.8 s | smart write refinement, bus timing benchmark |
| r6 | 13.6 s | 22.7 s | smart write refinement |
| r7 | 13.6 s | 22.2 s | skip reading blocks that will be overwritten; flush logging |
| r8 | 13.6 s | **13.9 s** | **one volume flush per project save** |
| r9 | | | card read-verify test at faster bus timings (diagnostic) |
| r10 | 12.9 s | 13.8 s | no wasted zero-filling of cache blocks |
| r11 | 12.8 s | 12.0 s | zero-fill skip for overwritten blocks, sample RAM loop, card IDENTIFY logging, USB wait (part 1) |
| r12 | 12.3 s | 13.6 s | USB wait (part 2); final profiler build |

Save times vary by about 1.5 s from run to run (r11 and r12 have the same save code). r2 has no separate save profile, and r9's timings are not comparable because its diagnostic test ran at the start of every operation.

### r1: profiler and audio mute fix

The profiler itself, plus the first fix found with it: file operations mute audio through a begin/end pair, and every begin muted and waited again even when a begin was already active. Now only the outermost begin mutes and waits. ([R12_CHANGES.md](R12_CHANGES.md), change 7)

The first save profile showed where the time was: most of it in saving the 16 songs (about 22 s) and the library (about 3 s), file after file.

### r2 to r6: smart write

The FAT driver caches the card in 16 KB blocks and, on every file close, writes back whole dirty blocks: both FAT copies and the directory block, 96 sectors, even when one sector changed. With 505 files per project, that adds up.

Smart write (r2) puts a wrapper on the card's write function that keeps a shadow of what has been written and sends only the sectors that actually differ. r3 added read and write sector counters to the profiler to measure the effect. r4 to r6 reworked and refined it. The final version does not shadow a window's first write, so the 32 shadow windows stay available for the FAT and directory sectors that are rewritten again and again, and it handles the stock FAT mirror flush, which sends a stray tail from a neighbouring block into FAT 2. r4 also added a benchmark variant of the IDE read loop, and r5 a timing benchmark for the IDE bus (measured: status register read about 355 ns, uncached SDRAM write about 130 ns).

Result: save 33.5 s to 22.7 s. ([R12_CHANGES.md](R12_CHANGES.md), change 3)

### r7: skip reading blocks that will be overwritten

When a file is overwritten, the FAT driver asked the cache for each sector in "existing data" mode, so on a miss the cache read the whole 16 KB block from the card, only for the write loop to overwrite all of it. r7 switches the request to "fresh data" mode when the write covers the whole block. r7 also logged every volume flush together with its callers. ([R12_CHANGES.md](R12_CHANGES.md), change 5)

### r8: one volume flush per project save

Every file close flushes the whole volume: FAT 1, FAT 2, the FAT info sector, data and directory, about four extra card writes per file, about 530 times per project save. r8 makes file closes during a project save update the directory entry in the cache only, and flushes the volume once when the save finishes.

Result: save 22.2 s to 13.9 s, the biggest single gain of the project. ([R12_CHANGES.md](R12_CHANGES.md), change 4)

### r9: bus timing check (diagnostic)

A test that reads 64 KB at the driver's own timing as a reference, then again at faster bus settings, and compares the data. It was used to check whether the card could run faster than the v4 timing. The v4 timing was kept, and the test was removed in r10.

### r10: no wasted zero-filling

When a clean cache block was recycled, the OS reset it and filled all 16 KB with zeros, even though a full read from the card normally overwrites it immediately. r10 zero-fills only when no full read follows. ([R12_CHANGES.md](R12_CHANGES.md), change 6)

### r11: smaller gains

- No zero-filling of blocks that r7 has already marked as completely overwritten.
- Sample RAM transfer loop: the same 128 writes to the sound chip with 4 instructions per word instead of 7. ([change 8](R12_CHANGES.md))
- USB connect: the device-side detach wait is 250 ms instead of 1000 ms (two of the four wait constants). ([change 9](R12_CHANGES.md))
- The profiler logs the CF card's IDENTIFY data, to see whether multi-sector transfers could be used.

### r12: final profiler build

The same USB wait change for the remaining two wait constants. With this, the profiled save was down to 12 to 13.6 s from 33.5 s in r1.

## r12_clean: the everyday build

All r12 speed changes, with every development tool removed: profiler, timing-file writer, stage markers, sector counters, flush and event logging, card IDENTIFY logging, the bus benchmarks and the benchmark read loop. 1,769 changed bytes against stock.

Stopwatch: **load 20 s to 15 s, save 35 s to about 13 to 14 s**, with every saved file verified identical. Details: [R12_CHANGES.md](R12_CHANGES.md).

## r13: cache-hit guard

Several rounds of static analysis after r12 found no remaining bottleneck worth a full second, so the next step was driven by data again: a matched pair of r12 profiles (one load and one save of the test project) and a read-only capture of the card's FAT and directory structures, taken straight after the save.

These showed that during project-save writes, the cache runs a preliminary "flush every dirty block" step before looking up the block being written, even when that block is already cached and dirty. r13 adds a small guard that skips that step in exactly that case and leaves every other case on the original code.

Stopwatch against r12_clean: **save about 14 s to about 12.5 s**, load unchanged, all files verified. Details: [r13 build notes](../builds/r13/BUILD_NOTES.md) and [hardware results](../builds/r13/HARDWARE_RESULTS.md).

## Builds that were not adopted

- **v2 FAT scan patch:** side branch, not continued.
- **Builds from another AI assistant (Google Gemini):** several builds were produced and tested in October 2026. The first versions reverted part of the r12 save code and changed the card read loop; the later ones, rebuilt from r12_clean, gave no measurable gain on the hardware. None were used.

## How the work was done

Reverse engineering, patch development and verification were done by the author together with AI coding assistants: Anthropic Claude (analysis, v1 to r12_clean, verification of every build) and OpenAI Codex (r13). Every build was checked against its declared changes before flashing and verified on the hardware afterwards.

## Next

- More firmware clean-ups, additions and changes beyond storage speed.
- Testing on more machines, cards and the original hard drive.
