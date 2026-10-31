import struct

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

targets = {
    0x695220: 'A2DP_IsVendorPeerSinkCodecValidLhdcV3',
    0x694e70: 'A2DP_ParseInfoLhdcV3',
    0x6970e0: 'A2DP_VendorSourceCodecIndexLhdcV3',
    0x6975a0: 'A2dpCodecConfigLhdcV3::setCodecConfig',
    0x69a1b0: 'A2dpCodecConfigLhdcV3::setPeerCodecCapabilities',
}

# Scan all 32-bit words for BL / B instructions
for i in range(0, len(code) - 4, 4):
    word = struct.unpack('<I', code[i:i+4])[0]
    # BL instruction: 0x94000000 mask 0xFC000000
    if (word & 0xFC000000) == 0x94000000:
        imm26 = word & 0x03FFFFFF
        if imm26 & 0x02000000:
            imm26 -= 0x04000000
        target = i + (imm26 << 2)
        if target in targets:
            print(f"Call to {targets[target]} at 0x{i:08x} (BL)")
    # B instruction: 0x14000000 mask 0xFC000000
    elif (word & 0xFC000000) == 0x14000000:
        imm26 = word & 0x03FFFFFF
        if imm26 & 0x02000000:
            imm26 -= 0x04000000
        target = i + (imm26 << 2)
        if target in targets:
            print(f"Jump to {targets[target]} at 0x{i:08x} (B)")
