import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

data = code[0x694a00:0x694bd0]
for insn in cs.disasm(data, 0x694a00):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
