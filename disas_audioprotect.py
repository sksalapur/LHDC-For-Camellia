import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    data = f.read()

cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
code = data[0x491e40:0x491e40+200]
for i in cs.disasm(code, 0x491e40):
    print(f'{hex(i.address)}: {i.mnemonic} {i.op_str}')
