import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

data = code[0x697b3c:0x697b90]
for insn in cs.disasm(data, 0x697b3c):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
