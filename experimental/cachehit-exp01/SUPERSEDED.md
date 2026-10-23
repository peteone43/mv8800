# Superseded by exp02

Do not use exp01 for a speed comparison. Its guard at 0x8C608B22 used `mov.b` to read r12's 32-bit big-endian save-active flag. With active=1 stored as `00 00 00 01`, the guard read zero and never activated the bypass. Both original test fixtures incorrectly stored a byte, masking the problem. Their passing reports did not validate the actual flag representation.

[Exp02](../cachehit-exp02/) changes that instruction to `mov.l`; both corrected fixtures store a 32-bit value, reject exp01, and pass exp02. The original exp01 files remain here as historical artifacts.
