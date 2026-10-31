import struct

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

target = 0x694ad0

for i in range(0, len(code) - 4, 4):
    word = struct.unpack('<I', code[i:i+4])[0]
    if (word & 0xFC000000) in (0x94000000, 0x14000000):
        imm26 = word & 0x03FFFFFF
        if imm26 & 0x02000000:
            imm26 -= 0x04000000
        tgt = i + (imm26 << 2)
        if tgt == target:
            print(f"Call/Jump to disableLhdc at 0x{i:08x}")
