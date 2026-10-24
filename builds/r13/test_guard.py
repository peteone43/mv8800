#!/usr/bin/env python3
"""Execute the assembled guard in QEMU's big-endian SH CPU emulator.

The real original-flush target is replaced only in this test ELF by a sentinel
that verifies arguments and supplies a chosen success/failure return value.
QEMU's Linux SH user emulator limits mappings to below 0x80000000. The code
is therefore tested at its P0 alias, relocating only the save-state and
fallback-target address literals. Every instruction and the caller-id literal
remain byte-identical; actual P1 addresses are checked separately at build time.
"""
import json, os, random, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
TOOLS=ROOT/'toolchain/root/usr/bin'
ENV=dict(os.environ,LD_LIBRARY_PATH=str(ROOT/'toolchain/root/usr/lib/x86_64-linux-gnu'))

def run(tool,*args):
    r=subprocess.run([str(TOOLS/tool),*map(str,args)],env=ENV,capture_output=True,text=True,timeout=60)
    if r.returncode:raise RuntimeError(f'{tool}: {r.returncode}\n{r.stdout}\n{r.stderr}')
    return r

def s16(x):
    x &= 65535
    return x | 0xffff0000 if x&0x8000 else x

def expected(c):
    active,caller,slot,state,ogen,egen,volume,evolume,start,lba,length,orig=c
    return bool(active&0xffffffff and caller==0x8c52508e and 4<=s16(slot)<=15
                and state&255==2 and s16(ogen)==s16(egen) and s16(evolume)==volume
                and lba>=start and lba<((start+(length&65535))&0xffffffff))

def cases():
    valid=[1,0x8c52508e,4,2,1,1,0,0,1000,1000,32,1]
    out=[]
    def add(c):out.append(c[:11]+[int(expected(c)),c[11]])
    for index,values in {
        0:[0,1,2,128,255,256,65536,0x01000000,0x80000000,0xffffffff],1:[0,0x8c52508e,0x8c525090,0x8c64b2ac],
        2:[0,1,3,4,5,14,15,16,32767,32768,65535],3:[0,1,2,3,127,128,255],
        4:[0,1,2,32767,32768,65535],5:[0,1,2,32767,32768,65535],
        6:[0,1,32768,0xffff8000,0xffffffff],7:[0,1,32768,65535],
        9:[0,999,1000,1001,1031,1032,1033,0x80000000,0xffffffff],
        10:[0,1,2,31,32,32768,65535],11:[0,1,7,0xffffffff],
    }.items():
        for v in values:c=valid.copy();c[index]=v;add(c)
    rng=random.Random(880013)
    for i in range(12000):
        slot=rng.randrange(4,16);gen=rng.randrange(65536);volume=rng.randrange(16)
        start=rng.randrange(0,0x10000000);length=rng.choice([1,2,16,32,64,65535]);lba=start+rng.randrange(length)
        c=[1,0x8c52508e,slot,2,gen,gen,volume,volume,start,lba,length,rng.choice([0,1,7,0xffffffff])]
        if i%2:
            j=rng.choice([0,1,2,3,4,5,6,7,8,9,10])
            c[j]=rng.choice([0,3,16,65535,0x80000000,0xffffffff])
        add(c)
    for start in [0x7ffffff0,0x80000000,0xfffffff0,0xffffffff]:
        for length in [0,1,16,32,65535]:
            for offset in [0,1,15,31,32,65534]:
                c=valid.copy();c[8]=start;c[9]=(start+offset)&0xffffffff;c[10]=length;add(c)
    return out

def main():
    cs=cases()
    payload=(ROOT/'guard.bin').read_bytes()
    test_payload=payload
    for old,new in [(0x8c608b18,0x0c608b18),(0x8c656de0,0x0c656de0)]:
        assert test_payload.count(old.to_bytes(4,'big'))==1
        test_payload=test_payload.replace(old.to_bytes(4,'big'),new.to_bytes(4,'big'))
    assert payload[:112]==test_payload[:112]
    (ROOT/'guard-test.bin').write_bytes(test_payload)
    table='\n'.join('    .long '+','.join(hex(v&0xffffffff) for v in c) for c in cs)
    source=r'''
    .section .text.test,"ax"
    .global _start
_start:
    mov.l .Ltable,r8
    mov.l .Lcount,r9
.Lnext:
    mov.l .Lobj,r10
    mov.l .Lframe,r14
    mov.l .Lhint,r1
    mov.l r1,@r14
    mov.l @(4,r8),r0
    mov.l r0,@(4,r14)
    mov.l @(8,r8),r0
    mov.w r0,@r1
    add #-4,r0
    extu.w r0,r0
    mov #11,r2
    cmp/hi r2,r0
    bf 1f
    mov #0,r0
1:  add #4,r0
    mov #12,r1
    mul.l r1,r0
    sts macl,r2
    mov.l .Lentries,r1
    mov.l r1,@(8,r10)
    add r1,r2
    mov.l @(32,r8),r0
    mov.l r0,@r2
    mov.l @(28,r8),r0
    mov r2,r1
    add #4,r1
    mov.w r0,@r1
    mov.l @(20,r8),r0
    add #2,r1
    mov.w r0,@r1
    mov.l @(12,r8),r0
    add #2,r1
    mov.b r0,@r1
    mov.l @(16,r8),r0
    mov r10,r1
    add #16,r1
    mov.w r0,@r1
    mov.l @(40,r8),r0
    add #4,r1
    mov.w r0,@r1
    mov.l @r8,r0
    mov.l .Lflag,r1
    mov.l r0,@r1
    mov.l @(48,r8),r0
    mov.l .Lorig_result,r1
    mov.l r0,@r1
    mov #0,r0
    mov.l .Lfallback_called,r1
    mov.l r0,@r1
    mov.l .Lbefore_sp,r1
    mov.l r15,@r1
    mov.l .Lmarker,r12
    mov.l @(36,r8),r11
    mov.l @(24,r8),r13
    mov r10,r4
    mov #1,r5
    mov.l .Lguard,r0
    jsr @r0
     nop
.Lafter_call:
    mov.l @(44,r8),r1
    tst r1,r1
    bt 2f
    cmp/eq #1,r0
    bra 3f
     nop
2:  mov.l @(48,r8),r1
    cmp/eq r1,r0
3:  bt 4f
    mov #1,r4
    bra .Lfail
     nop
4:  mov.l .Lfallback_called,r1
    mov.l @r1,r0
    mov.l @(44,r8),r1
    mov #1,r2
    sub r1,r2
    cmp/eq r2,r0
    bt 5f
    mov #2,r4
    bra .Lfail
     nop
5:  mov.l .Lobj,r0
    cmp/eq r0,r10
    bf .Lregister_fail
    mov.l @(36,r8),r0
    cmp/eq r0,r11
    bf .Lregister_fail
    mov.l .Lmarker,r0
    cmp/eq r0,r12
    bf .Lregister_fail
    mov.l @(24,r8),r0
    cmp/eq r0,r13
    bf .Lregister_fail
    mov.l .Lframe,r0
    cmp/eq r0,r14
    bf .Lregister_fail
    mov.l .Lbefore_sp,r0
    mov.l @r0,r0
    cmp/eq r0,r15
    bf .Lregister_fail
    sts pr,r0
    mov.l .Lafter_call_pc,r1
    cmp/eq r0,r1
    bf .Lregister_fail
    add #52,r8
    dt r9
    bt .Ldone
    bra .Lnext
     nop
.Lregister_fail:
    mov #3,r4
    bra .Lfail
     nop
.Ldone:
    mov #0,r4
.Lfail:
    mov #1,r3
    trapa #0x10
    nop
    .balign 4
.Ltable: .long case_table
.Lcount: .long CASE_COUNT
.Lobj: .long obj
.Lframe: .long frame
.Lhint: .long hint
.Lentries: .long entries
.Lflag: .long 0x0c608b18
.Lguard: .long 0x0c608b20
.Lorig_result: .long original_result
.Lfallback_called: .long fallback_called
.Lbefore_sp: .long before_sp
.Lafter_call_pc: .long .Lafter_call
.Lmarker: .long 0x12345678

    .section .text.sentinel,"ax"
    mov.l .Lsobj,r0
    cmp/eq r0,r4
    bf .Lstub_fail
    mov r5,r0
    cmp/eq #1,r0
    bf .Lstub_fail
    mov.l .Lscalled,r1
    mov #1,r0
    mov.l r0,@r1
    mov.l .Lsresult,r1
    rts
     mov.l @r1,r0
.Lstub_fail:
    mov #4,r4
    mov #1,r3
    trapa #0x10
    nop
    .balign 4
.Lsobj: .long obj
.Lscalled: .long fallback_called
.Lsresult: .long original_result

    .section .data.flag,"aw"
    .long 0
    .section .text.guardbytes,"ax"
    .incbin "guard-test.bin"
    .section .data.cases,"aw"
    .balign 4
case_table:
CASE_TABLE
    .section .bss.scratch,"aw",@nobits
    .balign 4
obj: .skip 64
frame: .skip 64
hint: .skip 4
entries: .skip 192
original_result: .skip 4
fallback_called: .skip 4
before_sp: .skip 4
'''.replace('CASE_COUNT',str(len(cs))).replace('CASE_TABLE',table)
    (ROOT/'test_guard.S').write_text(source)
    (ROOT/'test_guard.ld').write_text('''ENTRY(_start)
SECTIONS {
 . = 0x10000; .text : { *(.text.test) }
 . = ALIGN(4096); .data : { *(.data.cases) } .bss : { *(.bss.scratch) }
 . = 0x0c608b18; .saveflag : { *(.data.flag) }
 . = 0x0c608b20; .guard : { *(.text.guardbytes) }
 . = 0x0c656de0; .sentinel : { *(.text.sentinel) }
 /DISCARD/ : { *(.text) *(.data) *(.bss) *(.note*) *(.comment) }
}
''')
    # .incbin is relative to cwd. Only two absolute literals are relocated.
    r=subprocess.run([str(TOOLS/'sh4-linux-gnu-as'),'--isa=sh3','-big','-o','test_guard.o','test_guard.S'],cwd=ROOT,env=ENV,capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stderr)
    run('sh4-linux-gnu-ld','-EB','-T',ROOT/'test_guard.ld','-o',ROOT/'test_guard.elf',ROOT/'test_guard.o')
    r=run('qemu-sh4eb-static',ROOT/'test_guard.elf')
    result={'machine':'QEMU big-endian SH CPU','cases':len(cs),'expected_dirty_hits':sum(c[11] for c in cs),
            'expected_original_path':sum(not c[11] for c in cs),'exit_status':r.returncode,
            'instruction_bytes_identical_to_firmware_payload':True,
            'test_only_literal_relocations':{'0x8C608B18':'0x0C608B18','0x8C656DE0':'0x0C656DE0'},
            'flag_store_instruction':'mov.l r0,@r1 (32-bit big-endian)',
            'active_value_one_memory_bytes':'00 00 00 01',
            'checks':['32-bit save flag','file-write caller','hint bounds','dirty state','cache generation','volume id',
                      'unsigned LBA bounds and overflow','original success/failure propagation','fallback arguments',
                      'r10-r15 and PR preservation; r8/r9 loop integrity'],
            'scope':'Guard machine code only; original routine replaced by an argument-checking sentinel in the test ELF. No Roland hardware is emulated.'}
    (ROOT/'guard-test-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
