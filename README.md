# MV-8800 experimental firmware

This repository contains the experimental cache-hit-before-flush build based on `MV8800_r12_clean.PRG`. Hardware speed and file-integrity testing are still pending. Keep this build only if the MV-8800 A/B test saves at least 0.5 seconds, all saved files match, and chkdsk passes.

## Downloads

- [Experimental PRG](experimental/cachehit-exp01/MV8800_r12_cachehit_exp01.PRG)
- [ZIP with PRG and reports](experimental/cachehit-exp01/MV8800_r12_cachehit_exp01.zip)
- [Every changed decoded address range and old/new bytes](experimental/cachehit-exp01/CHANGES.md)
- [Scope, checks, and power-loss trade-off](experimental/cachehit-exp01/BUILD_NOTES.md)
- [Final verification report](experimental/cachehit-exp01/final-verification.json)

On a GitHub file page, use **Download raw file** to save the binary. The PRG must be exactly 4,194,304 bytes and have this SHA-256:

```text
085bfe4e76b78311eddaa0d87d2e1424dfb95b8b9992b566b8b8a5c06b8f796b
```

Rename a copy to `MV8800.PRG` only when ready to flash. Keep your original `r12_clean` file.

## Change and verification

Only the preliminary flush is bypassed when the existing hint identifies the requested dirty buffer during project-save file writes. Every guard miss follows the original path. Explicit/final flush behavior is unchanged.

All 1,769 existing stock-to-r12 changes in the decoded image remain unchanged. The experimental build adds exactly 123 differing decoded bytes in six declared ranges. Its header through offset 0x20043 is identical to r12_clean; it expands to 7,181,268 bytes; the compressed stream ends at exclusive offset 0x341521, before 0x3FFFF0; and its last two bytes remain F6 81.

Power loss can lose file data or folder-entry changes that r12_clean might already have flushed. The logical impact is not bounded by cache size. See BUILD_NOTES.md before using the experiment.

## Recreate the exact PRG locally

The self-contained Python builder uses only the standard library and checks both input hashes, all protected decoded bytes, every changed range, the compressed round trip, packaging limits, and the exact expected output SHA-256. It never flashes anything or writes to either source file. It creates a new output folder beside the script and refuses to overwrite an existing output folder.

```text
python mv8800_build_exp01.py "path/to/MV8800_r12_clean.PRG" "path/to/MV8800_stock.PRG"
```

The builder is in `experimental/cachehit-exp01/`. The original stock and r12_clean firmware inputs are not included. The guard assembly, linker script, disassembly, and original emulation-result reports are included for review. Reproducing the PRG with the builder does not rerun the original emulation tests and does not establish an on-device speed improvement.
