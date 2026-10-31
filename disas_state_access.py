import capstone
from parse_elf_symbols import parse_elf

symbols = sorted(parse_elf('miui_libbluetooth_jni.so'), key=lambda x: x[0])

def find_sym(addr):
    prev = None
    for val, size, name in symbols:
        if val <= addr:
            prev = (val, name)
        else:
            break
    return prev

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

for target in [0x5e7df0, 0x5e8350]:
    sym = find_sym(target)
    print(f"=== Function at {target:x} (nearest symbol: {sym}) ===")
    data = code[target:target+0xa0]
    for insn in cs.disasm(data, target):
        print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
