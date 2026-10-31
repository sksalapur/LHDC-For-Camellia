import capstone

with open('miui_libbluetooth_jni.so', 'rb') as f:
    data = bytearray(f.read())

# 1. Patch 17 instances of mov wX, #0x4C33 -> mov wX, #0x4C35
offsets_4c33 = [
    0x48aedc, 0x679b98, 0x679c98, 0x679d84, 0x679e08, 0x679f44,
    0x67a0a0, 0x67a198, 0x67a218, 0x67a298, 0x67a348, 0x67a3c8,
    0x67a448, 0x67a4f8, 0x67a578, 0x67a728, 0x694f84
]

for off in offsets_4c33:
    orig = data[off]
    assert orig in (0x68, 0x69, 0x6a), f"Unexpected byte at 0x{off:x}: 0x{orig:x}"
    new_byte = (orig & 0x1f) | 0xa0 # 0x68 -> 0xa8, 0x69 -> 0xa9, 0x6a -> 0xaa
    data[off] = new_byte

# 2. Patch movk at 0x6949d4 (movk x9, #0x4c33, lsl #32 -> movk x9, #0x4c35, lsl #32)
assert data[0x6949d4:0x6949d8] == bytes.fromhex('6986c9f2')
data[0x6949d4:0x6949d8] = bytes.fromhex('a986c9f2')

# 3. Patch length branch at 0x694eb4 (b.ne #0x694ff8 -> b.lo #0x694ff8 to accept length >= 11)
assert data[0x694eb4:0x694eb8] == bytes.fromhex('210a0054')
data[0x694eb4:0x694eb8] = bytes.fromhex('230a0054')

# 4. Patch build length at 0x697164 (mov w8, #0xb -> mov w8, #0xd)
assert data[0x697164:0x697168] == bytes.fromhex('68018052')
data[0x697164:0x697168] = bytes.fromhex('a8018052')

# 5. Patch sink version rejection at 0x69785c (b.eq #0x697b3c -> nop)
assert data[0x69785c:0x697860] == bytes.fromhex('00170054')
data[0x69785c:0x697860] = bytes.fromhex('1f2003d5')

# 6. Bypass ProcessSourceGetConfig gatekeeper at 0x48aee4 (b.ne #0x48af8c -> b #0x48af8c)
assert data[0x48aee4:0x48aee8] == bytes.fromhex('41050054')
data[0x48aee4:0x48aee8] = bytes.fromhex('2a000014')

# 7. Make btif_av_get_lhdc_codec_state always return 1 at 0x5c4030
assert data[0x5c4030:0x5c4038] == bytes.fromhex('484700b0080942f9')
data[0x5c4030:0x5c4038] = bytes.fromhex('20008052c0035fd6')

# 8. Make btif_lhdc_codec_is_supported always return 1 at 0x868eb0
assert data[0x868eb0:0x868eb8] == bytes.fromhex('ff4302d15e8600f8')
data[0x868eb0:0x868eb8] = bytes.fromhex('20008052c0035fd6')

# 9. Bypass SelectSourceCodec skip check at 0x48c588 (tbz w27, #0, #0x48c5b8 -> b #0x48c5b8)
assert data[0x48c588:0x48c58c] == bytes.fromhex('9b010036')
data[0x48c588:0x48c58c] = bytes.fromhex('0c000014')

with open('miui_libbluetooth_jni_patched.so', 'wb') as f:
    f.write(data)

print("Patch applied successfully to miui_libbluetooth_jni_patched.so!")

# Verify disassembled regions
cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

print("\n--- Verifying 0x48aee0-0x48aee8 ---")
for insn in cs.disasm(data[0x48aee0:0x48aee8], 0x48aee0):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")

print("\n--- Verifying 0x48c580-0x48c590 ---")
for insn in cs.disasm(data[0x48c580:0x48c590], 0x48c580):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")

print("\n--- Verifying btif_av_get_lhdc_codec_state (0x5c4030) ---")
for insn in cs.disasm(data[0x5c4030:0x5c4038], 0x5c4030):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")

print("\n--- Verifying btif_lhdc_codec_is_supported (0x868eb0) ---")
for insn in cs.disasm(data[0x868eb0:0x868eb8], 0x868eb0):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
