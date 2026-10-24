/* MV-8800 r12_clean: guarded pre-lookup flush bypass, SH-3 big-endian.
 * Called ONLY from 0x8C6574D8 by redirecting its literal at 0x8C657660.
 * r10 = cache object; r11 = requested logical sector; r13 = volume id;
 * r14 = existing cache-get frame, [r14] = hint pointer,
 * [r14+4] = saved cache-get caller PR (0x8C52508E for r12 file writes).
 * Does not write RAM. Preserves r8-r15 and PR. Uses scratch r0-r5, MACL.
 * Every failed guard tail-calls the original routine with r4=r10, r5=1.
 */
    .section .text.guard,"ax"
    .balign 4
    .global cache_hit_guard
cache_hit_guard:
    mov.l .Lsave_active,r0
    mov.l @r0,r0
    tst r0,r0
    bt .Loriginal

    mov.l @(4,r14),r0
    mov.l .Lfile_write_caller,r1
    cmp/eq r1,r0
    bf .Loriginal

    mov.l @r14,r1
    mov.w @r1,r0
    add #-4,r0
    extu.w r0,r0
    mov #11,r1
    cmp/hi r1,r0
    bt .Loriginal

    add #4,r0
    mov #12,r1
    mul.l r1,r0
    sts macl,r0
    mov.l @(8,r10),r1
    add r0,r1

    mov r1,r2
    add #8,r2
    mov.b @r2,r0
    cmp/eq #2,r0
    bf .Loriginal

    mov r1,r2
    add #6,r2
    mov.w @r2,r2
    mov r10,r3
    add #16,r3
    mov.w @r3,r3
    cmp/eq r3,r2
    bf .Loriginal

    mov r1,r2
    add #4,r2
    mov.w @r2,r2
    cmp/eq r13,r2
    bf .Loriginal

    mov.l @r1,r2
    cmp/hs r2,r11
    bf .Loriginal
    mov r10,r3
    add #20,r3
    mov.w @r3,r3
    extu.w r3,r3
    add r2,r3
    cmp/hs r3,r11
    bt .Loriginal

    rts
     mov #1,r0

.Loriginal:
    mov r10,r4
    mov #1,r5
    mov.l .Loriginal_flush,r0
    jmp @r0
     nop
    .balign 4
.Lsave_active:
    .long 0x8C608B18
.Lfile_write_caller:
    .long 0x8C52508E
.Loriginal_flush:
    .long 0x8C656DE0
    .global cache_hit_guard_end
cache_hit_guard_end:
