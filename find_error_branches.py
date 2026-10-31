import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

# setCodecConfig is 0x6975a0 to 0x69a1b0
data = code[0x6975a0:0x69a1b0]
error_targets = [0x698078, 0x698090]

for insn in cs.disasm(data, 0x6975a0):
    if insn.mnemonic.startswith('b'):
        # parse branch target
        if any(f"#{hex(tgt)}" in insn.op_str or f"#{hex(tgt)[2:]}" in insn.op_str for tgt in error_targets):
            print(f"Error branch at 0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
        elif insn.mnemonic == 'b' and any(tgt in insn.op_str for tgt in ['69807', '69808', '69809']):
            print(f"Direct jump to error at 0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
