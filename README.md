# MV-8800 OS 1.01 Speed Patches

Unofficial patched builds of the Roland MV-8800 system software (OS 1.01) that make project **loading and saving** much faster, especially on machines where a CF card replaces the internal hard drive.

The patches change how the MV-8800 moves data to and from its storage. They do not touch sound, sequencing or the user interface, and they do not change the project file format: saved project files were verified byte for byte against reference copies.

> **Status:** private development repository. Everything here has been tested on one MV-8800 (OS 1.01, CF card in place of the hard drive). See [Known issues](docs/KNOWN_ISSUES.md) before using any build.

## Results

Test project: *InitProj 060* (505 files, 16 songs, 128 library patches, about 10.6 MB of sample data). Times are stopwatch measurements on the hardware.

| Build | Load | Save (same name) | Notes |
| --- | --- | --- | --- |
| Roland OS 1.01 (stock) | about 20 s | about 35 s | baseline |
| **r12_clean** | 15 s | 13 to 15 s (avg about 14 s) | recommended build |
| exp02 | 15 s | 11.5 to 14 s (avg about 12.5 s) | experimental, see trade-off below |

That's about 25% faster loading and about 2.5 times faster saving with r12_clean. Every saved file was compared byte for byte against a reference: the patched builds write exactly the same project data as before. See [Testing and verification](docs/TESTING.md).

## Builds

| Build | File | Status | SHA-256 |
| --- | --- | --- | --- |
| **r12_clean** | [`builds/r12_clean/MV8800_r12_clean.PRG`](builds/r12_clean/MV8800_r12_clean.PRG) | Stable, recommended | `2e8555db2afa8799790a311ca4ffaf2399a7c0771e643b150137f0212d78c8da` |
| exp02 | [`experimental/cachehit-exp02/MV8800_r12_cachehit_exp02.PRG`](experimental/cachehit-exp02/MV8800_r12_cachehit_exp02.PRG) | Experimental, hardware-tested | `3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7` |
| exp01 | [`experimental/cachehit-exp01/`](experimental/cachehit-exp01/) | Superseded, do not use | `085bfe4e76b78311eddaa0d87d2e1424dfb95b8b9992b566b8b8a5c06b8f796b` |

All checksums are also in [`SHA256SUMS.txt`](SHA256SUMS.txt). Details of each build are in [docs/BUILDS.md](docs/BUILDS.md).

**exp02 trade-off:** exp02 holds some file and folder updates in memory slightly longer during a save. If power is lost in the middle of a save, files from that save are more likely to be missing or incomplete than with r12_clean. Let saves finish before switching off.

## Quick start

1. Back up your projects and keep a copy of Roland's original OS 1.01 file.
2. Download the build (on GitHub, open the `.PRG` file and use **Download raw file**).
3. Check that the file is exactly 4,194,304 bytes and that its SHA-256 matches the table above.
   - Windows: `certutil -hashfile MV8800_r12_clean.PRG SHA256`
   - macOS / Linux: `shasum -a 256 MV8800_r12_clean.PRG`
4. Rename it to `MV8800.PRG` and install it with the MV-8800's normal system update procedure.

Full instructions, including how to go back to the stock OS, are in [docs/INSTALL.md](docs/INSTALL.md).

## What was changed

r12_clean contains these changes to OS 1.01 (1,769 changed bytes in the 7.2 MB program image):

- **CF/IDE transfers:** sector data is copied by the CPU instead of a slow, polled per-sector DMA, and the IDE bus wait states are reduced.
- **Smart write:** the file system cache rewrites whole 16 KB blocks on every file close. The patch keeps a shadow of what is already on the card and only writes sectors that actually changed.
- **One flush per project save:** stock OS flushes the whole volume (both FAT copies, directory and data) after each of the roughly 530 files in a project save. During a save, the patch updates entries in memory and flushes once at the end.
- **No pointless reads and clears:** cache blocks that are about to be completely overwritten are no longer read from the card first or zero-filled.
- **Smaller fixes:** audio mute no longer repeats its wait when file operations are nested, a faster sample-RAM transfer loop, and a shorter USB disconnect wait (1000 ms to 250 ms).

exp02 adds one more change on top: during a project save it skips an early cache flush when the data being written is already in the cache.

The full explanation, with addresses, is in [docs/R12_CHANGES.md](docs/R12_CHANGES.md) and [experimental/cachehit-exp02/BUILD_NOTES.md](experimental/cachehit-exp02/BUILD_NOTES.md).

## Documentation

| Document | Contents |
| --- | --- |
| [docs/INSTALL.md](docs/INSTALL.md) | Verifying, installing and rolling back |
| [docs/BUILDS.md](docs/BUILDS.md) | Every build, its lineage and checksums |
| [docs/R12_CHANGES.md](docs/R12_CHANGES.md) | Each r12 change: what the stock OS does, what the patch does |
| [docs/TESTING.md](docs/TESTING.md) | How builds were measured and verified, with results |
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | Hardware, PRG file format, compression, card layout, patching method |
| [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) | Trade-offs, open questions and MV-8800 quirks |
| [docs/HISTORY.md](docs/HISTORY.md) | How the project developed, including approaches that were rejected |
| [CHANGELOG.md](CHANGELOG.md) | Build-by-build summary |
| [tools/README.md](tools/README.md) | Verification tools for your own tests |

## Repository layout

```text
builds/r12_clean/           recommended build
experimental/cachehit-exp02 current experimental build, its builder, tests and hardware report
experimental/cachehit-exp01 superseded experimental build (kept for history)
docs/                       documentation
tools/                      project checksum and card capture tools
reference/                  reference checksums of the test project
SHA256SUMS.txt              checksums of every PRG in this repository
```

## Disclaimer

This is an independent, unofficial project. It is not affiliated with, endorsed by or supported by Roland Corporation. Roland and MV-8800 are trademarks of Roland Corporation.

Installing modified system software is at your own risk. Back up your data first. A failed or interrupted update can leave the instrument unable to start until a working OS is installed again.

The MV-8800 system software is Roland's copyrighted work, and Roland's official OS 1.01 is available from [Roland's MV-8800 support page](https://www.roland.com/au/support/by_product/mv-8800/updates_drivers/bc905792-2358-42b7-8952-a049c70add0e/).

## Credits

Developed by PeteOne (Peter Kazimierski), with reverse engineering, patch development and verification done together with AI coding assistants (Anthropic Claude and OpenAI Codex). Hardware testing on the author's own MV-8800.
