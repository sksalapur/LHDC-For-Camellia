.text
.globl main
main:
    // Base address: 0x695028
    // Inputs: x19 = p_ie, x21 = p_codec_info
    ldrb w8, [x21]           // length of codec_info
    cmp w8, #13              // V5 if length >= 13
    b.ge .is_v5

    ldrb w8, [x21, #9]       // byte 9
    and w9, w8, #0xf         // V3 sample rate
    cbz w9, .is_v5           // if low nibble is 0, treat as V5

    // --- V3 PARSING ---
    strb w9, [x19, #6]       // p_ie->sampleRate = w9
    lsr w9, w8, #3
    and w9, w9, #2           // bit 4 -> 2 (24-bit)
    tst w8, #0x20            // bit 5 -> 1 (16-bit)
    cinc w9, w9, ne
    cmp w9, #0
    mov w10, #2
    csel w9, w10, w9, eq     // default to 2
    str w9, [x19, #8]        // p_ie->bits_per_sample = w9
    b .finish

.is_v5:
    // --- V5 PARSING ---
    // Byte 9 (P6): Sample Rate
    ldrb w8, [x21, #9]       // byte 9 (P6)
    mov w9, wzr
    tst w8, #0x04            // 96kHz in V5
    mov w10, #1              // 96kHz in V3
    csel w9, w10, w9, ne
    tst w8, #0x10            // 48kHz in V5
    orr w10, w9, #4          // 48kHz in V3
    csel w9, w10, w9, ne
    tst w8, #0x20            // 44.1kHz in V5
    orr w10, w9, #8          // 44.1kHz in V3
    csel w9, w10, w9, ne
    cmp w9, #0
    mov w10, #1              // default to 96kHz if none
    csel w9, w10, w9, eq
    strb w9, [x19, #6]       // p_ie->sampleRate = w9

    // Byte 10 (P7): Bits per sample
    ldrb w8, [x21, #10]      // byte 10 (P7)
    mov w9, wzr
    tst w8, #0x02            // 24-bit in V5
    mov w10, #2              // 24-bit in V3
    csel w9, w10, w9, ne
    tst w8, #0x01            // 16-bit in V5
    orr w10, w9, #1          // 16-bit in V3
    csel w9, w10, w9, ne
    cmp w9, #0
    mov w10, #2              // default to 24-bit if none
    csel w9, w10, w9, eq
    str w9, [x19, #8]        // p_ie->bits_per_sample = w9

.finish:
    mov w8, #8
    strb w8, [x19, #0xd]     // p_ie->sub_version = 8 (V4/V5)
    strb wzr, [x19, #0xe]    // max_bit_rate = 0
    strb wzr, [x19, #0x10]   // is_ar = 0
    strb wzr, [x19, #0x11]   // is_ll = 0
    mov w0, wzr              // return code 0 (SUCCESS)
    b 0x694ffc               // jump to epilogue
