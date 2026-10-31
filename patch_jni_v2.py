import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    data = bytearray(f.read())

# 1. Patch 17 instances of 0x4C33 -> 0x4C35
offsets_4c33 = [
    0x48aedc, 0x679b98, 0x679c98, 0x679d84, 0x679e08, 0x679f44,
    0x67a0a0, 0x67a198, 0x67a218, 0x67a298, 0x67a348, 0x67a3c8,
    0x67a448, 0x67a4f8, 0x67a578, 0x67a728, 0x694f84
]

for off in offsets_4c33:
    orig = data[off]
    assert orig in (0x68, 0x69, 0x6a), f"Unexpected byte at 0x{off:x}: 0x{orig:x}"
    data[off] = orig | 0xc0 # 0x68 -> 0xa8 (bit 6 toggled)

# 2. Patch length check at 0x694eb0 (cmp w8, #0xb -> cmp w8, #0xd)
assert data[0x694eb0:0x694eb4] == bytes.fromhex('1f2d0071')
data[0x694eb0:0x694eb4] = bytes.fromhex('1f350071')

# 3. Patch build length at 0x697164 (mov w8, #0xb -> mov w8, #0xd)
assert data[0x697164:0x697168] == bytes.fromhex('68018052')
data[0x697164:0x697168] = bytes.fromhex('a8018052')

# 4. Patch sink version rejection at 0x69785c (b.eq #0x697b3c -> nop)
assert data[0x69785c:0x697860] == bytes.fromhex('00170054')
data[0x69785c:0x697860] = bytes.fromhex('1f2003d5')

with open('miui_libbluetooth_jni_patched.so', 'wb') as f:
    f.write(data)

print("Patch applied successfully to miui_libbluetooth_jni_patched.so!")

# Verify disassembled regions
cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

print("\n--- Verifying 0x694eb0 ---")
for insn in cs.disasm(data[0x694eb0:0x694eb8], 0x694eb0):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")

print("\n--- Verifying 0x697160 ---")
for insn in cs.disasm(data[0x697160:0x697170], 0x697160):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")

print("\n--- Verifying 0x697858 ---")
for insn in cs.disasm(data[0x697858:0x697868], 0x697858):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
