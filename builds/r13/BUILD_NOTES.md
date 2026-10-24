# r13 build notes

r13 is r12_clean plus one change: a cache-hit guard that skips an unnecessary flush during project saves. No profiler code is included. Rename a copy of `MV8800_r13.PRG` to `MV8800.PRG` to install.

## What it changes

During a project save, each file write asks the data cache for the block it is about to write. Before looking the block up, the stock code first runs a scan that flushes every dirty block to the card. When the block being written is already cached and dirty, that preliminary flush is wasted work.

r13 redirects the literal at `0x8C657660` to a 124-byte SH-3 guard at `0x8C608B20`. The guard skips the preliminary all-dirty scan and flush only if all of these are true:

1. r12's 32-bit project-save flag at `0x8C608B18` is nonzero (read with `mov.l @r0,r0` at `0x8C608B22`).
2. The caller is r12's file-write helper (return address `0x8C52508E` in the caller's stack frame).
3. The cache hint points at a data slot (4 to 15) whose state is exactly dirty (2).
4. The hint's cache generation, volume id and unsigned sector bounds match the request exactly, using the same comparisons as the original cache-hit code.

On a match it returns success to `0x8C6574DC`, and the original cache-access code still validates the volume and hint, returns the cache pointer and performs the write. On any mismatch it tail-calls the original `0x8C656DE0` with r4 = cache object and r5 = 1, so the original return value and error path are unchanged. The guard writes no RAM and allocates no memory. It preserves r8 to r15 and PR; r0 to r5, MACL and the condition flags are scratch at this call point.

The guard occupies the unreachable remainder of the old function at `0x8C608AA0` that r12 had already replaced. r12's wrappers and save-state words up to `0x8C608B1F` are untouched, and the next original function starts at `0x8C608BB0`. No function-pointer literals point into the guard area.

r12's save flag is written by existing r12 code: set at `0x8C608ADC` (`mov #1,r0`) / `0x8C608ADE` (`mov.l r0,@r8`), cleared at `0x8C608AE8` / `0x8C608AEA`. See [r12-save-flag-disassembly.txt](r12-save-flag-disassembly.txt).

## Changed bytes

All 1,769 bytes that differ between stock and r12_clean are unchanged. r13 adds exactly 123 changed bytes in six ranges, listed with old and new bytes in [CHANGES.md](CHANGES.md), [unpacked-changes.tsv](unpacked-changes.tsv) and [unpacked-changes.json](unpacked-changes.json). Bytes inside the 124-byte guard that happen to equal the original are not counted.

## Packaging checks

- PRG bytes `0x000000` to `0x020043` are identical to r12_clean.
- The program image expands to exactly 7,181,268 bytes.
- The compressed stream ends at `0x341521` (exclusive), 781,007 bytes before the `0x3FFFF0` limit.
- The PRG is exactly 4,194,304 bytes and the 16-byte trailer (ending `F6 81`) is preserved.
- The stream decodes to exactly the intended image in two independent decoders. No undeclared changes exist.

## Emulation tests

- The guard was assembled with GNU as (SH-3, big-endian) and linked at its real firmware address: [cache_hit_guard.S](cache_hit_guard.S), [guard.ld](guard.ld), [guard-disassembly.txt](guard-disassembly.txt).
- 12,193 guard cases passed in QEMU's big-endian SH emulator: guard misses, signed-word and unsigned-sector edge cases, fallback arguments, original success and failure returns, and register, stack and PR preservation ([guard-test-results.json](guard-test-results.json), [test_guard.py](test_guard.py)).
- 18 integration cases ran the actual original cache-access and all-dirty routines with and without the guard. The qualifying dirty hit skips the flush; other callers, calls outside a save, hint misses, clean hits, bounds misses, mode exclusions and flush errors behave exactly as before ([integration-test-results.json](integration-test-results.json), [test_integration.py](test_integration.py)).
- The save flag is stored as a full 32-bit word in both test fixtures, exactly as r12 stores it.
- Limits: QEMU user mode cannot map the firmware's P1 addresses, so test-only absolute addresses were rebased to P0 aliases (guard instruction bytes unchanged). The volume lookup, division, allocation and physical flush services were test stubs, not Roland hardware emulation.

## Hardware results

Save of the test project about 14 s to about 12.5 s, load unchanged at 15 s, all files verified. See [HARDWARE_RESULTS.md](HARDWARE_RESULTS.md).

## Power-loss trade-off

The preliminary flush can now happen later. During that time, file data or folder-entry changes that r12_clean would already have written can still be in RAM. A power cut during a save can leave files missing or incomplete, and the effect is not limited by the cache's byte size. Cache capacity and the explicit and final flush code are unchanged.

## Checksums

```text
r13 PRG SHA-256        3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7
r12_clean SHA-256      2e8555db2afa8799790a311ca4ffaf2399a7c0771e643b150137f0212d78c8da
```

## Rebuilding

[build_r13.py](build_r13.py) recreates the exact PRG from the stock OS 1.01 file and r12_clean, using only the Python standard library. It checks both input hashes, all protected bytes, every changed range, the packaging limits, the round-trip decode and the final SHA-256. It never writes to the input files and refuses to overwrite an existing output folder.

```text
python build_r13.py MV8800_r12_clean.PRG MV8800_stock.PRG
```

The emulation tests need the GNU SH toolchain, QEMU and the unpacked r12 image; the builder needs only Python.
