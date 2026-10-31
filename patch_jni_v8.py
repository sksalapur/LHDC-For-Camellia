import struct
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

# 10. Fix incoming SET_CONFIGURATION rejection on reconnect at 0x6adaac (b.ne #0x6adb00 -> nop)
assert data[0x6adaac:0x6adab0] == bytes.fromhex('a1020054')
data[0x6adaac:0x6adab0] = bytes.fromhex('1f2003d5')

def extract_text(elf_path):
    with open(elf_path, 'rb') as f:
        elf_data = f.read()
    e_shoff = struct.unpack('<Q', elf_data[40:48])[0]
    e_shentsize = struct.unpack('<H', elf_data[58:60])[0]
    e_shnum = struct.unpack('<H', elf_data[60:62])[0]
    e_shstrndx = struct.unpack('<H', elf_data[62:64])[0]
    shstr_offset = struct.unpack('<Q', elf_data[e_shoff + e_shstrndx*e_shentsize + 24 : e_shoff + e_shstrndx*e_shentsize + 32])[0]
    for i in range(e_shnum):
        sh = elf_data[e_shoff + i*e_shentsize : e_shoff + (i+1)*e_shentsize]
        name_idx = struct.unpack('<I', sh[:4])[0]
        name = elf_data[shstr_offset + name_idx:].split(b'\0')[0].decode('utf-8')
        if name == '.text':
            sh_offset = struct.unpack('<Q', sh[24:32])[0]
            sh_size = struct.unpack('<Q', sh[32:40])[0]
            return bytearray(elf_data[sh_offset:sh_offset+sh_size])
    raise ValueError(f"No .text section found in {elf_path}")

# 11. Dynamic LHDC V5 capability framing in A2DP_VendorInitCodecConfigLhdcV3 (0x697204 - 0x697280)
patch11_code = extract_text('patch11.elf')
assert len(patch11_code) <= 124, f"patch11_code too large: {len(patch11_code)} > 124"
nop_count = (124 - len(patch11_code)) // 4
patch11_full = patch11_code + bytes.fromhex('1f2003d5') * nop_count
assert len(patch11_full) == 124
data[0x697204:0x697280] = patch11_full

# At 0x697290: strb w8, [x19, #0xb] -> nop
assert data[0x697290:0x697294] == bytes.fromhex('682e0039')
data[0x697290:0x697294] = bytes.fromhex('1f2003d5')

# 12. Patch A2DP_ParseInfoLhdcV3
# At 0x694f90: b #0x695028 (26 00 00 14)
assert data[0x694f90:0x694f94] == bytes.fromhex('a8264039') # ldrb w8, [x21, #9]
data[0x694f90:0x694f94] = bytes.fromhex('26000014')

patch12_code = extract_text('patch_parse.elf')
assert len(patch12_code) <= 464, f"patch12_code too large: {len(patch12_code)}"

# Calculate branch at the end of patch12_code to 0x694ffc
last_pc = 0x695028 + len(patch12_code) - 4
target = 0x694ffc
diff_inst = (target - last_pc) // 4
branch_bytes = struct.pack('<I', 0x14000000 | (diff_inst & 0x03ffffff))
patch12_code[-4:] = branch_bytes

# Write patch12_code into 0x695028
data[0x695028:0x695028+len(patch12_code)] = patch12_code

# Safety fallback at 0x6951f8: mov w0, wzr; b #0x694ffc
data[0x6951f8:0x695200] = bytes.fromhex('1f00805280ffff17')

# 13. Bypass SCMS-T check in FindPeerSink at 0x48bc50 (b.eq #0x48bcd0 -> b #0x48bcd0)
assert data[0x48bc50:0x48bc54] == bytes.fromhex('00040054')
data[0x48bc50:0x48bc54] = bytes.fromhex('20000014')

# Also at 0x48bc60: tbnz w0, #0, #0x48bcfc -> b #0x48bcfc
assert data[0x48bc60:0x48bc64] == bytes.fromhex('e0040037')
data[0x48bc60:0x48bc64] = bytes.fromhex('27000014')

with open('miui_libbluetooth_jni_patched.so', 'wb') as f:
    f.write(data)

print("Patch applied successfully to miui_libbluetooth_jni_patched.so (v8)!")

# Verify disassembled regions
cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

print("\n--- Verifying Patch 13 FindPeerSink SCMS-T Bypass (0x48bc48 - 0x48bc70) ---")
for insn in cs.disasm(data[0x48bc48:0x48bc70], 0x48bc48):
    print(f"0x{insn.address:08x}: {insn.mnemonic:10s} {insn.op_str}")
