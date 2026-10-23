# MV8800_r12_cachehit_exp01.PRG

Experimental cache-hit-before-flush build from the uploaded MV8800_r12_clean.PRG. No profiler or r13 modifications are included. Rename a copy to MV8800.PRG for flashing.

The only functional change redirects the literal at 0x8C657660 to a 124-byte SH-3 guard at 0x8C608B20. The guard skips the preliminary all-dirty scan/flush only if:

1. r12's project-save flag at 0x8C608B18 is nonzero.
2. The existing cache-get caller saved in its real stack frame is r12's file-write helper return address 0x8C52508E.
3. The hint's slot is 4 through 15 and its state is exactly dirty (2).
4. Its cache generation, volume id, and unsigned logical-sector bounds match the request exactly, using the same comparisons as the original cache-hit body.

On that hit it returns success to 0x8C6574DC; the original cache-access body still validates the volume and hint, returns the cache pointer, and performs the file write. Every failed guard tail-calls the original 0x8C656DE0 with r4=cache object and r5=1; its original return value and failure path remain intact. The guard neither writes RAM nor allocates memory. It preserves r8–r15 and PR; r0–r5, MACL and condition flags are scratch at this existing call point.

The guard occupies an unreachable remainder of the old function at 0x8C608AA0 that r12 already replaced. The existing r12 wrappers and save-state words through 0x8C608B1F remain untouched. The next original function starts at 0x8C608BB0. No literal function-pointer references into the new guard space were found; apparent incoming branch encodings in nearby literal data were disassembled and checked rather than treated as executable instructions.

All 1,769 bytes differing between stock and r12_clean in the decoded image are unchanged. There are exactly 123 newly differing bytes in six ranges, fully listed with old/new bytes in CHANGES.md, unpacked-changes.tsv and unpacked-changes.json. Bytes equal by coincidence inside the 124-byte payload are not listed as differences. Original firmware inputs are untouched.

Packaging checks:

- PRG bytes 0x000000–0x020043 are byte-identical to r12_clean.
- Expanded image is exactly 7,181,268 bytes.
- Compressed stream ends at exclusive offset 0x341521 (last consumed byte 0x341520), before 0x3FFFF0 by 781,007 bytes.
- PRG is exactly 4,194,304 bytes.
- Last two bytes are F6 81; the complete original 16-byte trailer is preserved.
- The new stream round-trips to the exact intended decoded image in the established ring decoder and a separate history/distance decoder. No undeclared decoded changes exist.

Validation:

- GNU assembler restricted to SH-3, big-endian; linked at actual firmware addresses.
- 12,188 guard cases passed in QEMU's big-endian SH instruction emulator, including guard misses, signed-word and unsigned-LBA edge cases, fallback arguments, original success/failure returns, and register/stack/PR preservation.
- 18 additional integration cases executed the actual original cache-access and all-dirty instruction bodies, both with and without the guard, confirming that the qualifying dirty hit skips the flush and other callers, outside-save calls, hint misses, clean hits, bounds misses, mode exclusions and miss-side flush errors follow their original behavior.
- QEMU Linux cannot map the firmware's P1 addresses, so test-only absolute address literals were rebased to P0 aliases. Guard instruction bytes were unchanged. Called volume lookup, division, allocation and physical-flush services were controlled test stubs, not Roland hardware emulation.

No on-device gain or file/checksum/chkdsk result is claimed. The hardware acceptance criterion remains at least 0.5 s net saving, no file differences, and successful same-name/new-name save and chkdsk checks.

Power-loss trade-off: the preliminary flush can occur later. During that interval, file data or folder-entry changes that r12_clean might already have written can remain in RAM. A cut can leave files missing or incomplete; the logical effect is not bounded by the cache's byte capacity. Existing cache capacity and explicit/final flush code are unchanged.

PRG SHA-256:
085bfe4e76b78311eddaa0d87d2e1424dfb95b8b9992b566b8b8a5c06b8f796b

Base r12_clean SHA-256:
2e8555db2afa8799790a311ca4ffaf2399a7c0771e643b150137f0212d78c8da

Reproduction: build.py assembles, patches only the two declared areas, repacks and verifies. test_guard.py and test_integration.py execute the emulation checks; verify_build.py independently verifies the final output and manifest. All are in the parent experimental-build directory. Machine-readable results are alongside this document.
