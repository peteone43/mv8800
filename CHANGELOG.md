# Changelog

Times are for the test project *InitProj 060* on the author's MV-8800 (OS 1.01, CF card).

## exp02 (experimental), 2026-10-23

- Adds a cache-hit guard on top of r12_clean: during a project save, the cache's preliminary flush of all dirty blocks is skipped when the requested block is already cached and dirty. Every other case follows the original code.
- 123 changed bytes in six ranges; all 1,769 r12 bytes unchanged.
- Hardware: save about 14 s to about 12.5 s, load unchanged at 15 s. 505/505 files identical after same-name saves; read-only chkdsk clean.
- Trade-off: on power loss mid-save, slightly more of that save can be lost than with r12_clean.
- SHA-256 `3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7`

## exp01 (superseded), 2026-10-23

- First version of the cache-hit guard. Read only one byte of the 32-bit save flag, so it never activated. Do not use.

## r12_clean (recommended), October 2026

- The r12 storage speed changes with the development profiler removed.
- IDE transfers by CPU copy instead of polled DMA; reduced IDE wait states.
- Smart write: only changed sectors are written back to the card.
- One volume flush per project save instead of one per file.
- No reading or zero-filling of cache blocks that are about to be overwritten.
- Audio mute no longer repeats its wait when file operations are nested.
- Faster sample RAM transfer loop; USB connect wait 1000 ms to 250 ms.
- Hardware: load about 20 s to 15 s, save about 35 s to 13 to 14 s.
- SHA-256 `2e8555db2afa8799790a311ca4ffaf2399a7c0771e643b150137f0212d78c8da`

## Development builds (not released)

- **v1:** one-byte waveform patch.
- **v2:** FAT cluster-chain scan patch (side branch, not continued).
- **v3:** IDE transfers by CPU copy.
- **v4:** IDE bus timing.
- **r1 to r12:** profiler builds used to develop and measure the r12 changes.
