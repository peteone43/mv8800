#!/usr/bin/env python3
"""Checksum and compare MV-8800 project folders (.PRJ).

Used to prove that a firmware build saves projects byte for byte the same as a
reference build. Read-only: it never writes to the project folders.

  make     FOLDER [-o manifest.json]   record md5, sha256 and size of every file
  compare  A B                         A and B are project folders or manifests

Exit code 0 when everything matches, 1 when anything differs.

MV-8800 pads project folder names with spaces to 12 characters, so quote the path:
  python project_checksums.py compare "L:\\PROJECTS\\TA          .PRJ" "L:\\PROJECTS\\TB          .PRJ"
"""
import argparse
import hashlib
import json
import os
import sys


def scan(folder):
    files = {}
    for root, _, names in os.walk(folder):
        for name in names:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, folder).replace(os.sep, '/')
            data = open(path, 'rb').read()
            files[rel] = {'size': len(data),
                          'md5': hashlib.md5(data).hexdigest(),
                          'sha256': hashlib.sha256(data).hexdigest(),
                          'path': path}
    return files


def load(src):
    if os.path.isdir(src):
        return scan(src), True
    man = json.load(open(src))
    return {k: dict(v) for k, v in man['files'].items()}, False


def first_last_diff(pa, pb):
    a, b = open(pa, 'rb').read(), open(pb, 'rb').read()
    idx = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    if len(a) != len(b):
        idx.append(min(len(a), len(b)))
    return idx


def cmd_make(args):
    files = scan(args.folder)
    man = {'folder': os.path.basename(os.path.normpath(args.folder)),
           'file_count': len(files),
           'files': {k: {f: v[f] for f in ('size', 'md5', 'sha256')} for k, v in sorted(files.items())}}
    text = json.dumps(man, indent=1) + '\n'
    if args.output:
        open(args.output, 'w').write(text)
        print('wrote %s (%d files)' % (args.output, len(files)))
    else:
        sys.stdout.write(text)
    return 0


def cmd_compare(args):
    a, a_dir = load(args.a)
    b, b_dir = load(args.b)
    only_a, only_b = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    differ = []
    for k in sorted(set(a) & set(b)):
        key = 'sha256' if 'sha256' in a[k] and 'sha256' in b[k] else 'md5'
        size_differs = 'size' in a[k] and 'size' in b[k] and a[k]['size'] != b[k]['size']
        if a[k][key] != b[k][key] or size_differs:
            differ.append(k)
    print('A: %s (%d files)' % (args.a, len(a)))
    print('B: %s (%d files)' % (args.b, len(b)))
    print('identical: %d' % (len(set(a) & set(b)) - len(differ)))
    for k in only_a:
        print('only in A: ' + k)
    for k in only_b:
        print('only in B: ' + k)
    for k in differ:
        line = 'differs:   ' + k
        if a_dir and b_dir:
            idx = first_last_diff(a[k]['path'], b[k]['path'])
            line += '  (%d byte(s), first 0x%X, last 0x%X)' % (len(idx), idx[0], idx[-1])
        print(line)
    ok = not (only_a or only_b or differ)
    print('RESULT: ' + ('all files match' if ok else 'differences found'))
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('make', help='write a checksum manifest for a project folder')
    m.add_argument('folder')
    m.add_argument('-o', '--output')
    c = sub.add_parser('compare', help='compare two project folders or manifests')
    c.add_argument('a')
    c.add_argument('b')
    args = p.parse_args()
    sys.exit(cmd_make(args) if args.cmd == 'make' else cmd_compare(args))


if __name__ == '__main__':
    main()
