import struct

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

target = 0xef7a96
target_page = target & ~0xfff
target_off = target & 0xfff

# Find ADRP to target_page
for i in range(0, len(code) - 4, 4):
    word = struct.unpack('<I', code[i:i+4])[0]
    if (word & 0x9F000000) == 0x90000000:
        immlo = (word >> 29) & 3
        immhi = (word >> 5) & 0x7ffff
        imm = (immhi << 2) | immlo
        if imm & 0x100000: imm -= 0x200000
        page = (i & ~0xfff) + (imm << 12)
        if page == target_page:
            # check next instruction for target_off
            next_word = struct.unpack('<I', code[i+4:i+8])[0]
            # ldrb / strb immediate offset
            print(f"ADRP to 0x{page:x} at 0x{i:08x}, next instruction 0x{next_word:08x}")
