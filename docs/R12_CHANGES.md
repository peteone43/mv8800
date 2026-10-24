# r12_clean changes

r12_clean differs from Roland OS 1.01 in 1,769 bytes of the decoded program image. New code is placed in unused areas of the image ("code caves"), and the original code is redirected to it by changing call targets or function-pointer literals. Addresses below are program addresses (the image runs at `0x8C010000`).

Background on how the MV-8800 stores files: the OS has its own FAT32 driver with a cache of 16 slots of 16 KB each. Slots 0 to 3 hold FAT sectors, slots 4 to 15 hold directory and file data. A project save writes about 530 files (128 library patches, 16 songs with 16 patches each, sequences, mixer and effect settings, the sample file and so on), so anything the OS does per file is multiplied by 530.

## 1. IDE data transfer by CPU copy (v3)

**Stock:** each 512-byte sector moving to or from the card is transferred with the DMA controller in 64-word chunks, while the CPU busy-polls the DMA controller until each chunk is done. The CPU gains nothing from the DMA and pays the setup cost every time.

**Patch:** the PIO data-in and data-out routines copy the sector directly with the CPU. Same bus timing and the same uncached buffer access the DMA used.

**Where:** data-in at `0x8C610ED0`, data-out at `0x8C611094` (90 bytes each).

## 2. IDE bus timing (v4)

**Stock:** the bus area used for the IDE interface is set to 10 wait states, with a 3.5-cycle data setup time.

**Patch:** 6 wait states (WCR2, `0x8C6127C6`) and a 2.5-cycle setup time (PCR, `0x8C6127B3`). The hold time is unchanged. No transfer errors were seen during testing with the CF card in use; slower cards have not been tested.

## 3. Smart write

**Stock:** on every file close, the FAT driver writes back whole dirty cache slots: both FAT copies (2 x 32 sectors) and the directory slot (32 sectors), even if only one sector changed.

**Patch:** a wrapper on the ATA device write entry point (`0x8C615B50`) keeps a shadow copy of what has been written to the card, in 16 KB windows keyed by device and starting sector (32 windows, about 512 KB of RAM). When a cache slot is written again, only the sectors that differ from the shadow are sent to the card.

Rules that keep the shadow correct (a valid shadow sector always equals the sector on the card):

- a write from a cache slot first invalidates the same sectors in every other window, then sends only the sectors that changed and updates the shadow
- the first time a window is written, its sectors are written normally and their data is not copied into the shadow, because most file data is written only once; this keeps the 32 windows for the FAT and directory sectors that are rewritten again and again
- any other write (USB mass storage, large direct writes) invalidates every overlapping shadow sector and is passed through
- non-ATA devices (the CD drive) are passed through untouched
- the stock FAT mirror flush sends a stray tail from the neighbouring cache slot into FAT 2 and then overwrites it with the correct data; the wrapper sends only the part inside the slot

**Where:** code at `0x8C4E9940`, `0x8C64B040` and `0x8C65D090`. The four pointers to the device write function (`0x8C616514`, `0x8C617070`, `0x8C6457B8`, `0x8C699E64`) point to the wrapper.

## 4. One volume flush per project save

**Stock:** every file close calls the FAT file flush, which updates the directory entry and then flushes the whole volume: FAT 1, FAT 2, FAT info sector, data and directory. That is about four extra card writes per file, about 530 times per project save.

**Patch:** while a project save is running, file closes update the directory entry in the cache without flushing the volume, and the volume is remembered. When the save finishes, the volume is flushed once. Outside project saves nothing changes.

**Where:** wrapper code at `0x8C608AA0` to `0x8C608B1F`. The project-save calls at `0x8C4341F8` and `0x8C435930` go through the wrapper, and the file-flush pointer at `0x8C62B988` points to it. The "save in progress" flag is the 32-bit word at `0x8C608B18`.

This was the biggest single gain: in the profiler, the save of the test project dropped from about 22 s to about 14 s.

## 5. Skip reading cache blocks that will be overwritten

**Stock:** when a file is overwritten, the FAT write loop asks the cache for each sector in "existing data" mode. On a cache miss the cache reads the whole 16 KB block from the card, and the write loop then overwrites all of it.

**Patch:** when the sector is the first in its block, the block lies within the current cluster, and at least a whole block of data is left to write, the request is switched to "fresh data" mode, which skips the read.

**Where:** `0x8C64CBC0` (16 bytes), helper code at `0x8C524FE0`.

## 6. No wasted zero-filling of cache blocks

**Stock:** when a clean cache block is recycled, the OS resets its header and fills all 16 KB with zeros, even though a full read from the card normally overwrites it immediately.

**Patch:** recycling only resets the header. The block is zero-filled only in the cases where no full read follows (a fresh cluster that is expected to be zero, or a read cut short at the end of the volume), and not at all when change 5 has already established that the write covers the whole block.

**Where:** helper code at `0x8C556B50`. The recycle call literal at `0x8C657098` and the read literal at `0x8C657670` are redirected.

## 7. Audio mute nesting

**Stock:** file operations mute audio through a begin/end pair. Each begin mutes and waits, even when a begin is already active, so nested file operations repeat the mute and its wait.

**Patch:** only the outermost begin mutes and waits. The nesting counter still counts every begin and end.

**Where:** `0x8C4F2ED0` (6 bytes).

## 8. Sample RAM transfer loop

**Stock:** the inner loop that writes 128 words to the sound chip port uses 7 instructions per word, including two stack accesses.

**Patch:** the same 128 writes in the same order, with the pointer kept in a register: 4 instructions per word.

**Where:** `0x8C011832` (14 bytes).

## 9. USB connect wait

**Stock:** connecting USB waits 1000 ms for the device-side detach, on both connect paths.

**Patch:** 250 ms. The waits are constants used only by their own functions (`0x8C6496E2`, `0x8C64971C`, `0x8C649768`, `0x8C64979C`).

## 10. Waveform patch (v1)

A single byte at `0x8C4B825F` (`0x0F` to `0x7F`), carried over from the build this project started from.

## What r12_clean does not include

The development builds also carried a 2 ms sampling profiler, a timing-file writer, stage markers, sector counters, an event log, flush logging, card IDENTIFY logging and a benchmark variant of the read loop. All of these were removed for r12_clean. The v2 FAT cluster-chain scan patch is also not included.

## Complete list of changed areas

| Start | End | Bytes | Change |
| --- | --- | --- | --- |
| `0x8C011832` | `0x8C01183F` | 14 | 8 Sample RAM loop |
| `0x8C1B2060` | `0x8C1B2063` | 4 | placeholder return used instead of the profiler's event logger |
| `0x8C4341F9` | `0x8C4341FB` | 3 | 4 save call redirect |
| `0x8C435931` | `0x8C435933` | 3 | 4 save call redirect |
| `0x8C4B825F` | `0x8C4B825F` | 1 | 10 waveform patch |
| `0x8C4E9951` | `0x8C4E9B77` | 551 | 3 smart write code |
| `0x8C4F2ED0` | `0x8C4F2ED5` | 6 | 7 audio mute nesting |
| `0x8C524FE0` | `0x8C5250AB` | 204 | 5 read-skip helper |
| `0x8C556B50` | `0x8C556C17` | 200 | 6 zero-fill helper |
| `0x8C608AA0` | `0x8C608B1F` | 128 | 4 save flush deferral |
| `0x8C610ED0` | `0x8C610F29` | 90 | 1 IDE data-in |
| `0x8C611094` | `0x8C6110ED` | 90 | 1 IDE data-out |
| `0x8C6127B3` | `0x8C6127B3` | 1 | 2 IDE setup time |
| `0x8C6127C6` | `0x8C6127C6` | 1 | 2 IDE wait states |
| `0x8C616515` | `0x8C616517` | 3 | 3 device write redirect |
| `0x8C617071` | `0x8C617073` | 3 | 3 device write redirect |
| `0x8C62B989` | `0x8C62B98B` | 3 | 4 file flush redirect |
| `0x8C6457B9` | `0x8C6457BB` | 3 | 3 device write redirect |
| `0x8C6496E2` | `0x8C6496E3` | 2 | 9 USB wait |
| `0x8C64971C` | `0x8C64971D` | 2 | 9 USB wait |
| `0x8C649768` | `0x8C649769` | 2 | 9 USB wait |
| `0x8C64979C` | `0x8C64979D` | 2 | 9 USB wait |
| `0x8C64B040` | `0x8C64B16B` | 300 | 3 smart write code |
| `0x8C64CBC0` | `0x8C64CBCF` | 16 | 5 read-skip hook |
| `0x8C657099` | `0x8C65709B` | 3 | 6 recycle redirect |
| `0x8C657671` | `0x8C657673` | 3 | 6 read redirect |
| `0x8C65D096` | `0x8C65D13F` | 170 | 3 smart write code and state |
| `0x8C699E65` | `0x8C699E67` | 3 | 3 device write redirect |

Ranges list the first and last changed byte; bytes inside a range that happen to equal the original are not counted in the 1,769 total.
