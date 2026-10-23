# MV-8800 experimental firmware

This repository contains the experimental cache-hit-before-flush build based on `MV8800_r12_clean.PRG`. Final owner-reported MV-8800 tests measured **about 1.5 seconds faster per save**, with project load unchanged. Same-name file comparisons and read-only CHKDSK passed. The save-as comparison has one unresolved field difference in `PROJECT_.MV0`, described below. `r12_clean` remains the owner's fallback build.

**Current build: exp02.** Exp01 is superseded: it read the first byte of a 32-bit big-endian save flag and therefore did not activate the bypass. Exp02 reads the full flag with `mov.l`. The corrected 32-bit-store fixtures reject exp01; exp02 passes 12,193 guard and 18 integration cases.

## Final hardware results

Stopwatch results for InitProj 060, using same-name saves:

| Build | Load | Three saves | Mean save |
| --- | --- | --- | --- |
| r12_clean | 15 s | 15 / 13.5 / 13.5 s | about 14 s |
| exp02 | 15 s | 14 / 12 / 11.5 s | about 12.5 s |

The roughly 1.5 s saving exceeds the 0.5 s acceptance threshold. All 505 files matched reference checksums after three exp02 same-name saves. In a save-as comparison with Song 1 tempo changed to 110 BPM, both projects contained 505 files: 504 were byte-identical, including `SONG01/SEQUENCE.MV0`. Only `PROJECT_.MV0` differed: the expected project-name letter and bytes `0x28–0x2A`. The latter field may reflect runtime state, but its meaning and run-to-run consistency are unconfirmed; no repeat exp02 save-as was performed. Read-only CHKDSK found no problems.

See [the complete hardware report](experimental/cachehit-exp02/HARDWARE_RESULTS.md) for the exact file differences, the owner's code investigation, CHKDSK results, and the retained power-loss trade-off. No further tests or firmware changes were performed for this documentation update.

## Downloads

- [Experimental PRG](experimental/cachehit-exp02/MV8800_r12_cachehit_exp02.PRG)
- [Original build ZIP with PRG and pre-hardware reports](experimental/cachehit-exp02/MV8800_r12_cachehit_exp02.zip)
- [Every changed decoded address range and old/new bytes](experimental/cachehit-exp02/CHANGES.md)
- [Scope, checks, and power-loss trade-off](experimental/cachehit-exp02/BUILD_NOTES.md)
- [Final verification report](experimental/cachehit-exp02/final-verification.json)

The ZIP, firmware, and build-verification JSON remain the original build artifacts. The final hardware results are recorded separately in `HARDWARE_RESULTS.md`.

On a GitHub file page, use **Download raw file** to save the binary. The PRG must be exactly 4,194,304 bytes and have this SHA-256:

```text
3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7
```

Rename a copy to `MV8800.PRG` only when ready to flash. Keep your original `r12_clean` file.

## Change and verification

Only the preliminary flush is bypassed when the existing hint identifies the requested dirty buffer during project-save file writes. Every guard miss follows the original path. Explicit/final flush behavior is unchanged.

All 1,769 existing stock-to-r12 changes in the decoded image remain unchanged. The experimental build adds exactly 123 differing decoded bytes in six declared ranges. Its header through offset 0x20043 is identical to r12_clean; it expands to 7,181,268 bytes; the compressed stream ends at exclusive offset 0x341521, before 0x3FFFF0; and its last two bytes remain F6 81.

Power loss can lose file data or folder-entry changes that r12_clean might already have flushed. The logical impact is not bounded by cache size. See BUILD_NOTES.md before using the experiment.

## Recreate the exact PRG locally

The self-contained Python builder uses only the standard library and checks both input hashes, all protected decoded bytes, every changed range, the compressed round trip, packaging limits, and the exact expected output SHA-256. It never flashes anything or writes to either source file. It creates a new output folder beside the script and refuses to overwrite an existing output folder.

```text
python mv8800_build_exp02.py "path/to/MV8800_r12_clean.PRG" "path/to/MV8800_stock.PRG"
```

The builder is in `experimental/cachehit-exp02/`. The original stock and r12_clean firmware inputs are not included. The guard assembly, linker script, disassembly, and original emulation-result reports are included for review. Reproducing the PRG with the builder does not rerun the original emulation tests and does not establish an on-device speed improvement.

The corrected test sources are included for review. Running those emulator fixtures requires the analysis workspace toolchain and unpacked r12 input; the standalone Python builder requires only your original stock/r12_clean PRGs and Python. See BUILD_NOTES.md for the exact flag-store instructions, test limitations, and exp01 regression results.
