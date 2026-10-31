import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

# search for instructions using immediate 11 (0xb) in LHDC code range (0x694000 to 0x69d000)
data = code[0x694bd0:0x69cd00]
for insn in cs.disasm(data, 0x694bd0):
    if '#0xb' in insn.op_str or ', 0xb' in insn.op_str or '#11' in insn.op_str:
        print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
