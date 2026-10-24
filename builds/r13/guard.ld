SECTIONS
{
    . = 0x8C608B20;
    .text : { *(.text.guard) }
    /DISCARD/ : { *(.text) *(.data) *(.bss) *(.comment) *(.note*) }
}
