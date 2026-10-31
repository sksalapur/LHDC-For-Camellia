import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

data = code[0x697b50:0x69a100]
error_destinations = [0x698078, 0x698088, 0x69808c, 0x698090]
for insn in cs.disasm(data, 0x697b50):
    if insn.mnemonic.startswith('b.'):
        # check target
        tgt_str = insn.op_str.split('#')[-1]
        try:
            tgt = int(tgt_str, 16)
            if tgt in error_destinations or (0x698070 <= tgt <= 0x6980a0):
                print(f"Error branch at 0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
        except:
            pass
    elif insn.mnemonic == 'b' and any(hex(d)[2:] in insn.op_str for d in error_destinations):
        print(f"Direct error jump at 0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
