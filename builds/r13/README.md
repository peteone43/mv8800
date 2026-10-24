# r13

Latest build: r12_clean plus a cache-hit guard that skips an unnecessary flush during project saves.

| | |
| --- | --- |
| File | `MV8800_r13.PRG` (rename to `MV8800.PRG` to install) |
| Size | 4,194,304 bytes |
| SHA-256 | `3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7` |
| MD5 | `90faf8aebff34b3c85101b567fb7fdb3` |
| Based on | r12_clean (all 1,769 r12 bytes unchanged) + 123 bytes |
| Measured | save about 14 s to about 12.5 s vs r12_clean, load unchanged |

**Trade-off:** if power is lost in the middle of a save, slightly more of that save can be lost than with r12_clean. Let saves finish before switching off.

| File | Contents |
| --- | --- |
| [BUILD_NOTES.md](BUILD_NOTES.md) | what the guard does, checks, emulation tests, rebuilding |
| [HARDWARE_RESULTS.md](HARDWARE_RESULTS.md) | timing and file-integrity results on the MV-8800 |
| [CHANGES.md](CHANGES.md) | every changed byte (old and new) |
| [build_r13.py](build_r13.py) | rebuilds the exact PRG from stock OS 1.01 and r12_clean |
| `cache_hit_guard.S`, `guard.ld`, `guard.bin`, `guard-disassembly.txt` | guard source, link script, binary, disassembly |
| `test_guard.py`, `test_integration.py`, `*-results.json` | emulation tests and results |
| `verification.json`, `final-verification.json`, `unpacked-changes.*` | machine-readable build reports |
