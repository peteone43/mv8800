"""Offline exact-build reproduction. Python standard library only; no flashing."""
import collections
import hashlib
import json
import sys
from pathlib import Path

R12_SHA = '2e8555db2afa8799790a311ca4ffaf2399a7c0771e643b150137f0212d78c8da'
STOCK_SHA = 'caa0af53eeb44536a695d8536417027745454bb69d4314eb23bd561ce9449726'
RESULT_SHA = '085bfe4e76b78311eddaa0d87d2e1424dfb95b8b9992b566b8b8a5c06b8f796b'
GUARD = bytes.fromhex(
    'd01b60002008892e50e1d11a30108b2a61e2601170fc600de10b301689237004'
    'e10c0017001a51a2310c62137208602088028b1862137206622163a373106331'
    '32308b1062137204622132d08b0b62123b228b0863a373146331633d332c3b32'
    '8901000be00164a3e501d003402b00098c608b188c52508e8c656de0')

def require(ok, message):
    if not ok:
        raise SystemExit('STOP: ' + message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def decode(raw):
    require(raw[0x20024:0x2002c] == b'LZ98L016', 'Wrong compression header')
    size = int.from_bytes(raw[0x20020:0x20024], 'big')
    require(size == 7181268, 'Wrong unpacked size')
    require(raw[0x20040:0x20044] == raw[0x20020:0x20024], 'Size headers differ')
    ring = bytearray(4096)
    out = bytearray()
    r, p = 0xfee, 0x20044
    while len(out) < size:
        flags = raw[p]
        p += 1
        for bit in range(8):
            if flags & (1 << bit):
                v = raw[p]
                p += 1
                out.append(v)
                ring[r] = v
                r = (r + 1) & 4095
            else:
                a, b = raw[p:p+2]
                p += 2
                pos = a | ((b & 240) << 4)
                for j in range((b & 15) + 3):
                    if len(out) == size:
                        break
                    v = ring[(pos+j) & 4095]
                    out.append(v)
                    ring[r] = v
                    r = (r+1) & 4095
            if len(out) == size:
                break
    return bytes(out), p

def encode(payload):
    data = bytes(0xfee) + payload
    index = {}
    def key(p):
        return (data[p] << 16) | (data[p+1] << 8) | data[p+2]
    def insert(p):
        old = p - 4096
        if old >= 0 and old+2 < len(data):
            k = key(old)
            q = index[k]
            require(q.popleft() == old, 'Compressor history mismatch')
            if not q:
                del index[k]
        if p+2 < len(data):
            index.setdefault(key(p), collections.deque()).append(p)
    for p in range(0xfee):
        insert(p)
    p, out = 0xfee, bytearray()
    while p < len(data):
        flag_offset = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if p == len(data):
                break
            best, best_pos = 0, 0
            limit = min(18, len(data)-p)
            if limit >= 3:
                for cand in reversed(index.get(key(p), ())):
                    n = 3
                    if data[cand:cand+limit] == data[p:p+limit]:
                        n = limit
                    else:
                        while n < limit and data[cand+n] == data[p+n]:
                            n += 1
                    if n > best:
                        best, best_pos = n, cand
                    if best == limit:
                        break
            length = best if best >= 3 else 1
            if best >= 3:
                pos = best_pos & 4095
                out.extend((pos & 255, ((pos >> 4) & 240) | (best-3)))
            else:
                flags |= 1 << bit
                out.append(data[p])
            for q in range(p, p+length):
                insert(q)
            p += length
        out[flag_offset] = flags
    return bytes(out)

def main():
    require(len(sys.argv) == 3, 'Usage: python mv8800_build_exp01.py R12_CLEAN.PRG STOCK.PRG')
    source = Path(sys.argv[1]).resolve()
    stock_path = Path(sys.argv[2]).resolve()
    raw, stock_raw = source.read_bytes(), stock_path.read_bytes()
    require(sha(raw) == R12_SHA, 'Input is not the verified r12_clean file')
    require(sha(stock_raw) == STOCK_SHA, 'Stock input does not match')
    old, _ = decode(raw)
    stock, _ = decode(stock_raw)
    cave, hook = 0x5f8b20, 0x647660
    require(len(GUARD) == 124, 'Guard was copied incorrectly')
    require(old[hook:hook+4] == bytes.fromhex('8c656de0'), 'Wrong hook bytes')
    new = bytearray(old)
    new[cave:cave+124] = GUARD
    new[hook:hook+4] = bytes.fromhex('8c608b20')
    protected = [i for i, (s, r) in enumerate(zip(stock, old)) if s != r]
    require(len(protected) == 1769, 'Unexpected r12 protection map')
    require(all(new[i] == old[i] for i in protected), 'Existing r12 change touched')
    spans = []
    for i, (a, b) in enumerate(zip(old, new)):
        if a != b:
            if spans and spans[-1][1] == i:
                spans[-1][1] = i+1
            else:
                spans.append([i, i+1])
    require(len(spans) == 6 and sum(b-a for a, b in spans) == 123, 'Wrong change ranges')
    require(all(cave <= a < b <= cave+124 or hook <= a < b <= hook+4
                for a, b in spans), 'Undeclared changes')
    print('Inputs verified. Compressing; please wait...', flush=True)
    packed = encode(bytes(new))
    end = 0x20044 + len(packed)
    require(end < 0x3ffff0, 'Compressed data is too large')
    result = raw[:0x20044] + packed + b'\xff'*(0x3ffff0-end) + raw[0x3ffff0:]
    decoded, verified_end = decode(result)
    require(decoded == new and verified_end == end, 'Round-trip verification failed')
    require(len(result) == 4194304 and result[-2:] == b'\xf6\x81', 'Wrong size or trailer')
    require(result[:0x20044] == raw[:0x20044], 'Header changed')
    require(end == 0x341521, 'Unexpected compressed end')
    require(sha(result) == RESULT_SHA, 'Output differs from the verified experimental build')
    require(source.read_bytes() == raw and stock_path.read_bytes() == stock_raw, 'Source file changed')
    changes = [{'start_address': f'0x{0x8c010000+a:08X}',
                'end_address_inclusive': f'0x{0x8c010000+b-1:08X}',
                'unpacked_offset': f'0x{a:X}', 'length': b-a,
                'old_bytes': old[a:b].hex(' ').upper(),
                'new_bytes': new[a:b].hex(' ').upper()} for a, b in spans]
    report = {'sha256': sha(result), 'prg_bytes': len(result),
              'decompressed_bytes': len(decoded), 'header_identical': True,
              'compressed_end_exclusive': hex(end), 'trailer': 'F6 81',
              'protected_bytes_checked': len(protected), 'protected_byte_violations': 0,
              'changed_unpacked_bytes': 123, 'changed_unpacked_ranges': 6,
              'matches_verified_experimental_build': True, 'original_files_unchanged': True}
    folder = Path(__file__).resolve().parent / 'MV8800_cachehit_exp01_output'
    require(not folder.exists(), 'Output folder exists; move it aside before retrying')
    folder.mkdir()
    firmware = folder / 'MV8800_r12_cachehit_exp01.PRG'
    with firmware.open('xb') as f:
        f.write(result)
    (folder / 'CHANGES.json').write_text(json.dumps(changes, indent=2)+'\n', encoding='utf-8')
    (folder / 'VERIFICATION.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    notes = ('Experimental cache-hit-before-flush build. No measured hardware speedup yet.\n'
             'Only bypasses the preliminary flush for a validated dirty hint hit during project-save '
             'file writes; every miss follows the original path. Final flush unchanged.\n'
             'Power loss can lose file data or folder entries that r12_clean might already have '
             'flushed; the logical loss is not bounded by cache size.\n'
             'Test same-name and new-name saves, all file checksums, and chkdsk. '
             'Keep only if measured saving is at least 0.5 seconds with no file differences.\n')
    (folder / 'BUILD_NOTES.txt').write_text(notes, encoding='utf-8')
    print('SUCCESS: exact verified experimental build. Nothing was flashed.')
    print('PRG:', firmware)
    print('SHA256:', sha(result))
    print('Change list and verification report:', folder)

if __name__ == '__main__':
    main()
