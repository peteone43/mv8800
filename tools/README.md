# Tools

Both tools need only Python 3 (standard library). Neither writes to the MV-8800 card.

## project_checksums.py

Checksums and compares MV-8800 project folders. Use it to check that a build saves your projects exactly as before.

```text
python project_checksums.py make "L:\PROJECTS\InitProj 060.PRJ" -o before.json
python project_checksums.py compare before.json "L:\PROJECTS\InitProj 060.PRJ"
python project_checksums.py compare "L:\PROJECTS\TA          .PRJ" "L:\PROJECTS\TB          .PRJ"
```

- `make` records the size, MD5 and SHA-256 of every file in a project folder.
- `compare` takes two folders, two manifests, or one of each. It lists files that exist on only one side and files whose contents differ. When both sides are folders it also shows how many bytes differ and the first and last differing offset.
- Exit code 0 means everything matches.

Example output:

```text
identical: 504
differs:   PROJECT_.MV0  (4 byte(s), first 0x1D, last 0x2A)
RESULT: differences found
```

The test project's reference manifest is [`../reference/InitProj060_reference.json`](../reference/InitProj060_reference.json).

## mv8800_meta_capture.py

Read-only capture of a card's FAT32 structures: the boot sector, reserved area, both FATs and every folder cluster. Used together with profiler output to see exactly which sectors a save rewrites.

Run from an Administrator command prompt on Windows, with the card as drive `L:`:

```text
python mv8800_meta_capture.py L
```

It opens the drive read-only and writes three files next to the script:

| File | Contents |
| --- | --- |
| `MV8800_meta_head.bin` | boot sector, reserved area and both FATs |
| `MV8800_meta_dirs.bin` | every folder cluster; each record is an 8-byte big-endian header (folder start cluster, this cluster) followed by the cluster bytes |
| `MV8800_meta_info.txt` | file system parameters and MD5 of both files |

It can also read a disk image file instead of a drive: `python mv8800_meta_capture.py card.img`.
