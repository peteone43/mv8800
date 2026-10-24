# Known issues and limitations

## Power loss during a save

The stock OS flushes the file system after every file it saves. r12_clean flushes once at the end of a project save (see [R12_CHANGES.md](R12_CHANGES.md), change 4), and r13 additionally delays one cache flush while files are written.

If power is lost in the middle of a project save, more of that save can be missing or incomplete than with the stock OS, and slightly more with r13 than with r12_clean. The logical effect is not limited by the cache size, because folder entries can be affected as well as file data. Projects that were already saved completely are not affected.

Let saves finish before switching off. This applies to every build, including stock.

## Tested on one machine

All hardware testing was done on one MV-8800 running OS 1.01 with a CF card in place of the internal hard drive. Not yet tested:

- the original internal hard drive
- other CF cards or CF adapters, especially slower cards (the IDE wait states are reduced, see change 2)
- MV-8800 units with other OS versions (the patches are for OS 1.01 only, and the builder checks for the exact OS 1.01 file)
- CD-ROM and USB workflows beyond normal use

Reports from other machines are welcome.

## `PROJECT_.MV0` runtime field (r13 save-as test)

In the save-as comparison between r12_clean and r13, bytes `0x28` to `0x2A` of `PROJECT_.MV0` differed. The OS fills this 32-bit field when a save starts, with the difference of two values it requests from a system service. It looks like a runtime status value rather than project data: other projects hold unrelated values there, and a project saved on another r12-based build has the same value as the r12_clean save. Whether r13 produces the same value on every save-as has not been tested yet.

## Memory use

Smart write keeps a 32-window shadow of recently written sectors, about 512 KB of RAM allocated from the OS heap.

## MV-8800 quirks (not caused by these patches)

- **chkdsk "`.` and/or `..`" errors.** On a card formatted by the MV-8800, Windows `chkdsk` (read-only) has reported six errors about the `.` and `..` entries of the root folders. This comes from how the MV-8800 formats folders. **Never run `chkdsk /f` on an MV-8800 card**: let the MV-8800 manage its own file system.
- **Space-padded folder names.** Project folders with names shorter than 12 characters are padded with spaces (`TA` is stored as `TA` plus 10 spaces). This is normal. Quote such paths on a computer.

## Development builds

The r1 to r12 profiler builds write timing files (`PROFL.BIN`, `PROFS.BIN`) to the card on every load and save. They are not included and are not meant for normal use.
