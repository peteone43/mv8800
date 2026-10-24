# Builds

All builds start from Roland's official MV-8800 OS 1.01 file.

| File | Size | SHA-256 |
| --- | --- | --- |
| Roland OS 1.01 `MV8800.PRG` (stock, not included) | 4,194,304 | `caa0af53eeb44536a695d8536417027745454bb69d4314eb23bd561ce9449726` |

The stock MD5 is `43cbfe509856e58b6b83b4a7ecd13fed`. The tools and builders in this repository check for this exact file.

## Released builds

### r12_clean (stable)

| | |
| --- | --- |
| File | [`builds/r12_clean/MV8800_r12_clean.PRG`](../builds/r12_clean/MV8800_r12_clean.PRG) |
| SHA-256 | `2e8555db2afa8799790a311ca4ffaf2399a7c0771e643b150137f0212d78c8da` |
| MD5 | `91ea4eb04b0f828aa73f6375a8cf851f` |
| Changed bytes vs stock | 1,769 (decoded program image) |
| Measured | load 20 s to 15 s, save 35 s to about 14 s |

The everyday build: all r12 speed changes with the development profiler removed. Contents are described in [R12_CHANGES.md](R12_CHANGES.md).

### r13 (latest)

| | |
| --- | --- |
| File | [`builds/r13/MV8800_r13.PRG`](../builds/r13/MV8800_r13.PRG) |
| SHA-256 | `3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7` |
| MD5 | `90faf8aebff34b3c85101b567fb7fdb3` |
| Based on | r12_clean, all 1,769 r12 bytes unchanged |
| Added | 123 changed bytes in six ranges (cache-hit guard) |
| Measured | save about 14 s to about 12.5 s vs r12_clean, load unchanged |

During a project save, skips the cache's preliminary "flush all dirty blocks" step when the block being written is already in the cache. Full notes: [BUILD_NOTES.md](../builds/r13/BUILD_NOTES.md), every changed byte: [CHANGES.md](../builds/r13/CHANGES.md), hardware report: [HARDWARE_RESULTS.md](../builds/r13/HARDWARE_RESULTS.md). Read the power-loss trade-off in [KNOWN_ISSUES.md](KNOWN_ISSUES.md) first.

r13 can be rebuilt exactly from the stock and r12_clean files with the standard-library Python builder [`build_r13.py`](../builds/r13/build_r13.py).

## Lineage

```text
Roland OS 1.01 (stock)
 └─ v1   waveform patch (1 byte)
     ├─ v2   FAT cluster-chain scan patch            (development branch, not continued)
     └─ v3   IDE transfers by CPU copy instead of DMA
         └─ v4   IDE bus timing
             └─ r1 to r12   profiler builds (development only)
                 └─ r12_clean   r12 speed changes, profiler removed
                     └─ r13     cache-hit guard
```

Intermediate builds are not included. Their checksums, for reference:

| Build | SHA-256 | Changed bytes vs stock |
| --- | --- | --- |
| v1 | `0c68211b8ef625b3d1aa2b7cab75a3f71881f5ef2ab3b6efe34a14fda2151f28` | 1 |
| v2 | `003d0eed492c5efa3e4d1be4ea1c52e265f48a848560e89f4fd32da0b496d5d2` | 501 |
| v3 | `1f62ee58388b7c298fc7e19fa0bfe09f9ca5c5fa3be053b623568ea4b2dbee65` | 179 |
| v4 | `0206ded2ae1874abbf0f445b8a76487cf2ef77f577a325763f029a0fb1953122` | 181 |

The r1 to r12 profiler builds add a 2 ms sampling profiler that writes timing files to the card. They were used to find where load and save time went and are not meant for normal use. What each revision changed is in [REVISIONS.md](REVISIONS.md).

## Builds that were evaluated and not adopted

Builds produced by another AI assistant (Google Gemini) were tested in October 2026. They gave no measurable speed gain on the hardware, and the first versions also reverted part of r12 and changed the card read loop. None of them are included. See [REVISIONS.md](REVISIONS.md).
