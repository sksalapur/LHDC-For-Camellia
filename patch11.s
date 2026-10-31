.text
.globl main
main:
    // Base address: 0x697204
    // Inputs: x0 = p_ie, x19 = sep_config->codec_info
    ldrb w8, [x0, #6]         // V3 sampleRate (bit 0=96k, bit 1=88.2k, bit 2=48k, bit 3=44.1k)
    mov w9, #0x10             // default 48kHz (0x10 in V5)
    tst w8, #1                // 96kHz? (bit 0 in V3)
    mov w10, #0x04            // 96kHz in V5
    csel w9, w10, w9, ne      // if 96kHz, w9 = 0x04
    tst w8, #8                // 44.1kHz? (bit 3 in V3)
    mov w10, #0x20            // 44.1kHz in V5
    csel w9, w10, w9, ne      // if 44.1kHz, w9 = 0x20
    strb w9, [x19, #9]        // Store V5 byte 9 (sample rate)

    ldrb w8, [x0, #8]         // V3 bits_per_sample (1=16-bit, 2=24-bit)
    mov w9, #2                // default 24-bit (0x02 in V5)
    tst w8, #1                // 16-bit? (bit 0 in V3)
    mov w10, #1               // 16-bit in V5 is 0x01
    csel w9, w10, w9, ne      // if 16-bit, w9 = 0x01
    strb w9, [x19, #0xa]      // Store V5 byte 10 (bits per sample)

    mov w8, #0x11             // V5 byte 11
    strb w8, [x19, #0xb]      // Store V5 byte 11
    strh wzr, [x19, #0xc]     // Store V5 bytes 12-13 (0x0000)
    mov w10, #0x24            // context restore for 0x697288
    mov w11, #0x3376          // context restore for 0x69728c
