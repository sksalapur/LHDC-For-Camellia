import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

def disas(addr, size):
    data = code[addr:addr+size]
    for insn in cs.disasm(data, addr):
        print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")

print("=== 0x694e70 (A2DP_ParseInfoLhdcV3 start) ===")
disas(0x694e70, 0x1a0)
