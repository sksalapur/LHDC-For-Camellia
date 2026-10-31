import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

def disas(addr, size):
    data = code[addr:addr+size]
    for insn in cs.disasm(data, addr):
        print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")

print("=== _Z28btif_lhdc_codec_is_supportedv (0x868eb0) ===")
disas(0x868eb0, 0xc0)

print("\n=== _ZN21A2dpCodecConfigLhdcV324setPeerCodecCapabilitiesEPKh (0x69a1b0) ===")
disas(0x69a1b0, 0x1e8)

print("\n=== _Z37A2DP_IsVendorPeerSinkCodecValidLhdcV3PKh (0x695220) ===")
disas(0x695220, 0x8c)
