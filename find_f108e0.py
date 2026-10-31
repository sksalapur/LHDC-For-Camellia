import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

# Find all ADRP instructions targeting page 0xf10000
for i in range(0, len(code)-4, 4):
    insn_data = code[i:i+4]
    for insn in cs.disasm(insn_data, i):
        if insn.mnemonic == 'adrp' and '0xf10000' in insn.op_str:
            # disasm next 5 instructions
            next_data = code[i:i+24]
            dis = list(cs.disasm(next_data, i))
            ops = [f"{d.mnemonic} {d.op_str}" for d in dis]
            if any('8e' in op or '8f' in op for op in ops):
                print(f"At 0x{i:08x}:")
                for d in dis[:4]:
                    print(f"  0x{d.address:08x}: {d.mnemonic} {d.op_str}")
