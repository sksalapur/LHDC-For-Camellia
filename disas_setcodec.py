import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

# Disassemble the first 120 instructions of setCodecConfig (0x6975a0)
data = code[0x6975a0:0x6975a0+0x300]
for insn in cs.disasm(data, 0x6975a0):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
