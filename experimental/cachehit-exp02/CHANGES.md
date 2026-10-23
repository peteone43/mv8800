# Complete decoded-image changes: r12_clean to exp02

Addresses are inclusive SH-3 runtime addresses; the OS base is 0x8C010000. Raw PRG differences from recompression are not listed, as requested. Exactly 123 bytes differ across these six ranges.

## 0x8C608B20–0x8C608B81 (98 bytes)

Unpacked offset: 0x5F8B20

Old bytes:

```text
20 08 89 06 D0 1B 95 2B 40 0B 54 E1 51 A3 31 00 8B 0E 2E B2 79 01 51 A1 39 17 8B E3 51 A3 41 11 8F 0E 64 A3 D0 15 A0 0D 65 D3 00 09 00 09 00 09 D1 11 2E 12 A0 09 E0 00 00 09 00 09 00 09 00 09 D0 0F 65 D3 66 C3 40 0B 57 E4 7E 14 6F E3 4F 26 6E F6 6D F6 6C F6 6B F6 6A F6 69 F6 00 0B 68 F6 00 CD
```

New bytes:

```text
D0 1B 60 02 20 08 89 2E 50 E1 D1 1A 30 10 8B 2A 61 E2 60 11 70 FC 60 0D E1 0B 30 16 89 23 70 04 E1 0C 00 17 00 1A 51 A2 31 0C 62 13 72 08 60 20 88 02 8B 18 62 13 72 06 62 21 63 A3 73 10 63 31 32 30 8B 10 62 13 72 04 62 21 32 D0 8B 0B 62 12 3B 22 8B 08 63 A3 73 14 63 31 63 3D 33 2C 3B 32 89 01
```

## 0x8C608B83–0x8C608B8F (13 bytes)

Unpacked offset: 0x5F8B83

Old bytes:

```text
09 8C 60 99 48 8C 60 9E 60 8C 5E 89 70
```

New bytes:

```text
0B E0 01 64 A3 E5 01 D0 03 40 2B 00 09
```

## 0x8C608B91–0x8C608B93 (3 bytes)

Unpacked offset: 0x5F8B91

Old bytes:

```text
5E 7F 20
```

New bytes:

```text
60 8B 18
```

## 0x8C608B95–0x8C608B97 (3 bytes)

Unpacked offset: 0x5F8B95

Old bytes:

```text
5E 06 60
```

New bytes:

```text
52 50 8E
```

## 0x8C608B99–0x8C608B9B (3 bytes)

Unpacked offset: 0x5F8B99

Old bytes:

```text
60 99 78
```

New bytes:

```text
65 6D E0
```

## 0x8C657661–0x8C657663 (3 bytes)

Unpacked offset: 0x647661

Old bytes:

```text
65 6D E0
```

New bytes:

```text
60 8B 20
```
