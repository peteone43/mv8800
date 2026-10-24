# Project history

## Goal

The MV-8800 is slow at loading and saving projects. On the test project, OS 1.01 took about 20 seconds to load and about 35 seconds to save, even with a fast CF card in place of the hard drive. The goal was to find out why and fix it in the system software, without changing anything the user sees or the files it writes.

## October 2026: from stock to r12

1. **Unpacking the OS.** The `MV8800.PRG` update file was decoded (Roland's LZ98 compression, see [TECHNICAL.md](TECHNICAL.md)) into the 7.2 MB SH-3 program image and loaded into Ghidra for analysis. A matching encoder was written so patched images could be packed back into a valid update file.
2. **Storage path (v1 to v4).** The IDE driver turned out to move every sector with a DMA transfer that the CPU busy-polled anyway, and the IDE bus ran with generous wait states. Replacing the DMA with a direct CPU copy (v3) and reducing the wait states (v4) sped up all card access. A FAT cluster-chain scan patch (v2) was tried on a side branch and not continued.
3. **Measuring instead of guessing (r1 to r12).** A sampling profiler was built into the OS: every 2 ms it records what the CPU is doing and writes the result to the card after each load or save. Each revision was flashed, timed and profiled. This showed that a project save is dominated by per-file overhead: about 530 files, each followed by a full file system flush and whole 16 KB cache blocks being rewritten.
4. **The fixes.** Smart write (send only changed sectors), one volume flush per project save instead of one per file, skipping reads and zero-fills of cache blocks that are about to be overwritten, plus smaller fixes. The single biggest gain was the flush change (r8): profiled save time dropped from about 22 s to about 14 s.
5. **r12_clean.** The final r12 changes were rebuilt without the profiler as the everyday build: load about 15 s, save about 13 to 14 s, with every saved file verified identical.

## Looking for the next second

Several further rounds of static analysis found no remaining bottleneck worth a full second, so the remaining work had to be profile-driven.

In parallel, another AI assistant (Google Gemini) was asked to produce further builds ("r13", "r13-clean", "r13-v2", "r13-v3"). They were checked byte by byte and tested on the hardware. The first versions reverted part of the r12 save code and changed the card read loop; the later ones, rebuilt from r12_clean, gave no measurable gain. None were adopted.

## October 23, 2026: exp02

OpenAI Codex was given a matched pair of profiles (one load and one save of the test project on the r12 profiler build) and a read-only capture of the card's FAT and directory structures taken straight after. From these it identified a preliminary "flush all dirty blocks" step in the cache that runs during project-save writes even when the block being written is already cached, estimated at roughly 0.7 s.

- **exp01** added a guard that skips that step only in that exact case. Review found the guard read one byte of a 32-bit big-endian flag, so it never activated, and the emulator tests had stored the flag the same wrong way. It was superseded.
- **exp02** fixed the flag read and the tests. On the hardware it saved the test project in about 12.5 s against about 14 s for r12_clean, with all files verified. See [HARDWARE_RESULTS.md](../experimental/cachehit-exp02/HARDWARE_RESULTS.md).

## How the work was done

Reverse engineering, patch development and verification were done by the author together with AI coding assistants: Anthropic Claude (firmware analysis, r1 to r12_clean, verification of every build) and OpenAI Codex (exp01 and exp02). Every build was checked against its declared changes before flashing and verified on the hardware afterwards.

## What's next

- More firmware clean-ups, additions and changes beyond storage speed.
- Testing on more machines, cards and the original hard drive.
