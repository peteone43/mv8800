# Read-only capture of the MV-8800 card's FAT32 structures (boot sector, FATs, all folder clusters).
# Opens the drive for READING ONLY. Nothing is ever written to the card.
# Usage (Administrator command prompt):  uv run --no-project mv8800_meta_capture.py [L]
# Output goes next to this script: MV8800_meta_head.bin, MV8800_meta_dirs.bin, MV8800_meta_info.txt
import os, sys, struct, hashlib

drive = (sys.argv[1] if len(sys.argv) > 1 else 'L').rstrip(':\\')
src = drive if os.path.isfile(drive) else '\\\\.\\' + drive + ':'
outdir = os.path.dirname(os.path.abspath(__file__))

f = open(src, 'rb')                                  # read-only handle
def read_at(off, n):
    f.seek(off)
    out = bytearray()
    while len(out) < n:
        b = f.read(min(1 << 20, n - len(out)))
        if not b:
            raise IOError('short read at %d' % (off + len(out)))
        out += b
    return bytes(out)

boot = read_at(0, 512)
bps, spc, rsvd, nfats = struct.unpack_from('<HBHB', boot, 11)
fatsz, = struct.unpack_from('<I', boot, 36)
rootc, = struct.unpack_from('<I', boot, 44)
if boot[510:512] != b'\x55\xaa' or boot[82:90] != b'FAT32   ' or bps not in (512, 1024, 2048, 4096):
    sys.exit('Not a FAT32 volume (or not readable): %r' % src)

head_len = (rsvd + nfats * fatsz) * bps
print('Reading boot sector, reserved area and %d FATs: %.1f MB ...' % (nfats, head_len / 1e6))
head = read_at(0, head_len)
fat = head[rsvd * bps: (rsvd + fatsz) * bps]
nent = len(fat) // 4
data0 = head_len
csize = spc * bps

def chain(c):
    seen = []
    while 2 <= c < 0x0FFFFFF8 and c < nent and c not in seen:
        seen.append(c)
        c = struct.unpack_from('<I', fat, 4 * c)[0] & 0x0FFFFFFF
    return seen

dirs_out = bytearray()
queue, done, ndirs = [rootc], set(), 0
while queue:
    start = queue.pop(0)
    if start in done:
        continue
    done.add(start)
    ndirs += 1
    end = False
    for c in chain(start):
        data = read_at(data0 + (c - 2) * csize, csize)
        dirs_out += struct.pack('>II', start, c) + data
        if end:
            continue
        for o in range(0, csize, 32):
            e = data[o:o + 32]
            if e[0] == 0:
                end = True
                break
            if e[0] == 0xE5 or e[11] == 0x0F or not (e[11] & 0x10) or e[:2] in (b'. ', b'..'):
                continue
            sc = (struct.unpack_from('<H', e, 20)[0] << 16) | struct.unpack_from('<H', e, 26)[0]
            if sc >= 2:
                queue.append(sc)

p = lambda n: os.path.join(outdir, n)
open(p('MV8800_meta_head.bin'), 'wb').write(head)
open(p('MV8800_meta_dirs.bin'), 'wb').write(dirs_out)
info = ('bytes_per_sector %d\nsectors_per_cluster %d\nreserved_sectors %d\nnum_fats %d\n'
        'fat_size_sectors %d\nroot_cluster %d\ndata_start_byte %d\nfolders %d\nfolder_clusters %d\n'
        'dirs.bin record = >II (folder start cluster, this cluster) + cluster bytes\n'
        'md5 head %s\nmd5 dirs %s\n') % (bps, spc, rsvd, nfats, fatsz, rootc, data0, ndirs,
        len(dirs_out) // (8 + csize), hashlib.md5(head).hexdigest(), hashlib.md5(dirs_out).hexdigest())
open(p('MV8800_meta_info.txt'), 'w').write(info)
f.close()
print(info)
print('Done. Nothing was written to the card.')
