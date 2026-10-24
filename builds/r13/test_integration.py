#!/usr/bin/env python3
"""Run the actual cache-get and all-dirty bodies with/without the new guard.

Only called services (volume lookup, divide, allocator, physical flush) are
test stubs. QEMU Linux requires P0 addresses, so absolute address literals
and the caller-id value are rebased; original SH instruction bytes are intact.
"""
import json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TOOLS=ROOT/'toolchain/root/usr/bin'
ENV=dict(os.environ,LD_LIBRARY_PATH=str(ROOT/'toolchain/root/usr/lib/x86_64-linux-gnu'))
OS=(ROOT.parent/'r12_clean.unpacked.bin').read_bytes();BASE=0x8c010000

def extract(start,end):return OS[start-BASE:end-BASE]
def literal_rebase(b,first=0):
    b=bytearray(b)
    for i in range(first,len(b)-3,4):
        v=int.from_bytes(b[i:i+4],'big')
        if 0x80000000<=v<0xa0000000:b[i:i+4]=(v-0x80000000).to_bytes(4,'big')
    return bytes(b)

SOURCE=r'''
    .section .text.test,"ax"
    .global _start
_start:
    mov.l .Lobj,r4
    mov.l .Lentries,r0
    mov.l r0,@(8,r4)
    mov.l .Lholder,r0
    mov.l r0,@(12,r4)
    mov r4,r1
    add #16,r1
    mov #1,r0
    mov.w r0,@r1
    add #4,r1
    mov #32,r0
    mov.w r0,@r1
    add #3,r1
    mov #1,r0
    mov.b r0,@r1
    mov.l .Lentries,r1
    mov #16,r2
1:  mov.l .Lbase_lba,r0
    mov.l r0,@r1
    mov r1,r3
    add #4,r3
    mov #0,r0
    mov.w r0,@r3
    add #2,r3
    mov #1,r0
    mov.w r0,@r3
    add #2,r3
    mov #2,r0
    mov.b r0,@r3
    add #12,r1
    dt r2
    bf 1b
    mov.l .Lentries,r1
    add #48,r1
    add #8,r1
    mov #STATE,r0
    mov.b r0,@r1
    mov.l .Lhint,r5
    mov #SLOT,r0
    mov.w r0,@r5
    mov #ACTIVE,r0
    mov.l .Lflag,r8
    mov.l r0,@r8
    mov #MODE,r1
    mov #0,r6
    mov.l .Lrequested_lba,r7
    mov.l .Ldriver,r0
    jsr @r0
     nop
    mov.l .Lexpected_result,r1
    cmp/eq r1,r0
    bt 2f
    mov #1,r4
    bra .Lexit
     nop
2:  mov.l .Lflush_count,r1
    mov.l @r1,r0
    cmp/eq #EXPECT_FLUSH,r0
    bt 3f
    mov #2,r4
    bra .Lexit
     nop
3:  mov.l .Lhint,r1
    mov.w @r1,r0
    extu.w r0,r0
    mov.l .Lexpected_hint,r1
    cmp/eq r1,r0
    bt 4f
    mov #3,r4
    bra .Lexit
     nop
4:  mov.l .Lentries,r1
    add #60,r1
    add #8,r1
    mov.b @r1,r0
    cmp/eq #EXPECT_OTHER_STATE,r0
    bt 5f
    mov #4,r4
    bra .Lexit
     nop
5:  mov #0,r4
.Lexit:
    mov #1,r3
    trapa #0x10
    nop
    .balign 4
.Lobj: .long obj
.Lentries: .long entries
.Lholder: .long holder
.Lhint: .long hint
.Lflag: .long 0x0c608b18
.Ldriver: .long DRIVER
.Lbase_lba: .long 1000
.Lrequested_lba: .long REQUESTED
.Lexpected_result: .long EXPECT_RESULT
.Lexpected_hint: .long EXPECT_HINT
.Lflush_count: .long flush_count

    .section .text.driver,"ax"
    sts.l pr,@-r15
    add #-4,r15
    mov.l r1,@r15
    mov.l .Lget,r0
    nop
    jsr @r0
     nop
    add #4,r15
    lds.l @r15+,pr
    rts
     nop
    .balign 4
.Lget: .long 0x0c6574b0

    .section .text.volume,"ax"
    mov.l .Lvol,r0
    rts
     nop
    .balign 4
.Lvol: .long volume
    .section .text.divide,"ax"
    rts
     mov #0,r0
    .section .text.allocator,"ax"
    rts
     mov #-1,r0
    .section .text.flush,"ax"
    mov.l .Lcount,r1
    mov.l @r1,r0
    add #1,r0
    mov.l r0,@r1
    mov #FLUSH_RESULT,r0
    tst r0,r0
    bt .Lflush_return
    mov.l @(8,r4),r1
    add #48,r1
    add #8,r1
    mov #12,r2
    mov #1,r0
1:  mov.b r0,@r1
    add #12,r1
    dt r2
    bf 1b
    mov #1,r0
.Lflush_return:
    rts
     nop
    .balign 4
.Lcount: .long flush_count
    .section .text.original,"ax"
    .incbin "integration-original.bin"
    .section .text.get,"ax"
    .incbin "integration-get.bin"
    .section .text.guardbytes,"ax"
    .incbin "integration-guard.bin"
    .section .data.flag,"aw"
    .long 0
    .section .bss.scratch,"aw",@nobits
    .balign 4
obj: .skip 64
entries: .skip 192
holder: .skip 64
hint: .skip 4
volume: .skip 128
flush_count: .skip 4
'''

def main():
    guard=literal_rebase((ROOT/'guard.bin').read_bytes(),112)
    assert guard[:112]==(ROOT/'guard.bin').read_bytes()[:112]
    (ROOT/'integration-guard.bin').write_bytes(guard)
    original=literal_rebase(extract(0x8c656de0,0x8c656e60),124)
    (ROOT/'integration-original.bin').write_bytes(original)
    tests=[
        ('dirty_hit',1,4,2,1,1000,1,False),
        ('outside_project_save',0,4,2,1,1000,1,False),
        ('other_caller',1,4,2,1,1000,1,True),
        ('hint_miss',1,16,2,1,1000,1,False),
        ('clean_hit',1,4,1,1,1000,1,False),
        ('upper_bound_miss',1,4,2,1,1032,1,False),
        ('mode_three',1,4,2,3,1000,1,False),
        ('miss_flush_failure',1,16,2,1,1000,0,False),
        ('last_sector_hit',1,4,2,2,1031,1,False),
    ]
    results=[]
    for patched in (False,True):
        get=bytearray(literal_rebase(extract(0x8c6574b0,0x8c657680),0x1b0))
        if patched:get[0x1b0:0x1b4]=(0x0c608b20).to_bytes(4,'big')
        (ROOT/'integration-get.bin').write_bytes(get)
        for name,active,slot,state,mode,lba,flush_result,other_caller in tests:
            valid_hit=slot==4 and 1000<=lba<1032
            skip=patched and active and not other_caller and state==2 and valid_hit and mode in (1,2)
            flush=int(mode in (1,2) and state==2 and not skip)
            success=valid_hit and not (flush and flush_result==0)
            expect_ptr=0x0daef1a0+4*16384+(lba-1000)*512 if success else 0
            other_state=1 if flush and flush_result else 2
            driver=0x0c5250a0 if other_caller else 0x0c525080
            values={'ACTIVE':active,'SLOT':slot,'STATE':state,'MODE':mode,'REQUESTED':lba,
                    'FLUSH_RESULT':flush_result,'EXPECT_FLUSH':flush,'EXPECT_RESULT':expect_ptr,
                    'EXPECT_HINT':slot if success else 65535,'EXPECT_OTHER_STATE':other_state,'DRIVER':driver}
            source=SOURCE
            import re
            for k,v in values.items():source=re.sub(r'\b'+k+r'\b',str(v),source)
            (ROOT/'integration.S').write_text(source)
            (ROOT/'integration.ld').write_text(f'''ENTRY(_start)
SECTIONS {{
 . = 0x10000; .text : {{ *(.text.test) }}
 . = ALIGN(4096); .bss : {{ *(.bss.scratch) }}
 . = {driver}; .driver : {{ *(.text.driver) }}
 . = 0x0c608b18; .flag : {{ *(.data.flag) }}
 . = 0x0c608b20; .guard : {{ *(.text.guardbytes) }}
 . = 0x0c650ea0; .volume : {{ *(.text.volume) }}
 . = 0x0c656de0; .original : {{ *(.text.original) }}
 . = 0x0c656f80; .allocator : {{ *(.text.allocator) }}
 . = 0x0c6574b0; .get : {{ *(.text.get) }}
 . = 0x0c657f30; .flush : {{ *(.text.flush) }}
 . = 0x0c6db610; .divide : {{ *(.text.divide) }}
 /DISCARD/ : {{ *(.text) *(.data) *(.bss) *(.note*) *(.comment) }}
}}
''')
            for tool,args in [('sh4-linux-gnu-as',['--isa=sh3','-big','-o','integration.o','integration.S']),
                              ('sh4-linux-gnu-ld',['-EB','-T','integration.ld','-o','integration.elf','integration.o']),
                              ('qemu-sh4eb-static',['integration.elf'])]:
                r=subprocess.run([str(TOOLS/tool),*args],cwd=ROOT,env=ENV,capture_output=True,text=True,timeout=30)
                if r.returncode:raise RuntimeError(f'{name} patched={patched} {tool}: {r.returncode}\n{r.stdout}\n{r.stderr}')
            results.append({'case':name,'patched':patched,'expected_flush_count':flush,'expected_success':success,'passed':True})
    result={'cases':len(results),'passed':len(results),'results':results,
            'save_flag_fixture':'32-bit mov.l r0,@r8, matching r12; active=1 stores 00 00 00 01',
            'scope':'Actual original cache-get and all-dirty SH instructions executed; service stubs only. P1-to-P0 address literals relocated for QEMU Linux. No Roland hardware emulation.'}
    (ROOT/'integration-test-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
