.text
.globl patch_parse_info
patch_parse_info:
    // x19 = p_ie, x21 = p_codec_info
    ldrb w8, [x21]
    cmp w8, #13
    b.ge .is_v5

    ldrb w8, [x21, #9]
    and w9, w8, #0xf
    cbz w9, .is_v5

    strb w9, [x19, #6]
    lsr w9, w8, #3
    and w9, w9, #2
    tst w8, #0x20
    cinc w9, w9, ne
    cmp w9, #0
    mov w10, #2
    csel w9, w10, w9, eq
    str w9, [x19, #8]
    b .common_flags

.is_v5:
    ldrb w8, [x21, #9]
    mov w9, #4
    tst w8, #0x20
    mov w10, #8
    csel w9, w10, w9, ne
    tst w8, #0x04
    mov w10, #1
    csel w9, w10, w9, ne
    strb w9, [x19, #6]

    ldrb w8, [x21, #10]
    mov w9, #2
    tst w8, #0x04
    mov w10, #1
    csel w9, w10, w9, ne
    str w9, [x19, #8]

.common_flags:
    mov w8, #8
    strb w8, [x19, #0xd]
    strb wzr, [x19, #0x10]
    strb wzr, [x19, #0x11]
    b .done

.done:
    nop
