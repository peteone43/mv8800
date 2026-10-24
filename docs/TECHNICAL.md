# Technical notes

## Hardware

| | |
| --- | --- |
| CPU | Hitachi/Renesas SH7709S (SH-3), big-endian |
| Program image | 7,181,268 bytes, runs at `0x8C010000` (P1, cached SDRAM) |
| Storage | internal IDE hard drive, here replaced by a CF card on an IDE adapter |
| Storage access | PIO through the SH bus area 6, OS-level FAT32 driver with its own cache |

## The `MV8800.PRG` file

The system update file is always 4,194,304 bytes (4 MiB).

| Offset | Contents |
| --- | --- |
| `0x000000` to `0x02003F` | loader code and build date string (`2008/04/14 21:10`) |
| `0x020040` to `0x020043` | decoded program length, big-endian `0x006D93D4` (7,181,268) |
| `0x020044` onward | compressed program image (LZ98) |
| up to `0x3FFFEF` | compressed stream must end before here; the rest is padded with `FF` |
| `0x3FFFF0` to `0x3FFFFF` | 16-byte trailer, ASCII `ECS05v1010b024` followed by `F6 81` |

None of the builds in this repository change the loader, the length word or the trailer.

### LZ98 compression

The program image is compressed with Roland's "LZ98" scheme, which is classic Okumura LZSS:

- 4 KB ring buffer, zero-filled, write position starting at `0xFEE`
- each flag byte covers the next 8 items, least significant bit first; 1 = literal byte, 0 = back-reference
- a back-reference is 2 bytes `b1 b2`: ring position `b1 | (b2 & 0xF0) << 4`, length `(b2 & 0x0F) + 3`

### How a patched PRG is built

1. Decode the stock PRG and record the input offset at every flag byte.
2. Apply the patches to the decoded image.
3. Find the first changed byte, keep the compressed stream unchanged up to the flag group before it, and re-encode only from there to the end.
4. Pad with `FF` to `0x3FFFF0`, append the original trailer.
5. Decode the result again and require it to equal the patched image exactly.

Keeping the stream prefix unchanged keeps the diff small and the loader's view of the file identical up to the first patch.

## Patching method

The OS image contains dead code (functions that are never called) and unused areas. New code goes there ("code caves"). Original behaviour is redirected by changing:

- function-pointer literals in a function's constant pool (most patches), or
- a few instructions in place, when the change is small (IDE timing, USB waits, mute fix, sample RAM loop).

Before a cave is used, the build scripts check that it still holds the original bytes and does not overlap another patch. Every redirected literal is checked against its original value before it is replaced.

All new code is SH-3 assembly, assembled for the exact address it runs at. It saves and restores the registers the calling convention requires (r8 to r15 and PR) and keeps the original function's return values and error paths.

## The card's file system

Measured on the test card (formatted by the MV-8800):

| | |
| --- | --- |
| File system | FAT32 |
| Sector / cluster | 512 bytes / 64 sectors (32 KB) |
| Reserved sectors | 32 |
| FATs | 2, 15,263 sectors each |
| Root directory | cluster 2 |
| Partition start | LBA 32 |

The OS's FAT driver caches the card in 16 slots of 16 KB: slots 0 to 3 for FAT sectors, 4 to 15 for directory and file data. Most of the r12 save speed-up comes from reducing how often these slots are written back. See [R12_CHANGES.md](R12_CHANGES.md).

### Project folders

A project is a folder `NAME.PRJ` in `PROJECTS`. Names shorter than 12 characters are padded with spaces (for example `TA` plus 10 spaces). `PROJECT_.MV0` and `PROJECTS\PROJLIST.MV0` store the name as 7-bit packed text. A typical project contains:

```text
PROJECT_.MV0  PATTERN_.MV0  PHRSLIST.MV0
LIBRARY\      CHORUS, CLIP, MFX, MTK, REVERB and PATCH001 to PATCH128
SAMPLE\       SAMPLE__.MV0 (all sample data)
SONG01.MV0\ to SONG16.MV0\
              CHORUS, MFX, MIXER, MTK, REVERB, SEQUENCE, SONGPRM and PATCH001 to PATCH016
```

That is 505 files, which is why per-file overhead dominates save time.

## Tools used

- Ghidra with GhidraMCP for disassembly and cross-references
- Python scripts for LZ98 decode/encode, an SH-3 assembler and disassembler, and an instruction-level emulator for testing new code against the original routines
- GNU binutils (SH-3, big-endian) and QEMU's SH emulator for the r13 guard tests
- An on-device sampling profiler (development builds only) and a read-only FAT32 capture script ([`tools/mv8800_meta_capture.py`](../tools/mv8800_meta_capture.py))
