import zlib, hashlib, struct

with open('classes_orig.dex', 'rb') as f:
    d = bytearray(f.read())

# 1. Patch BluetoothHeadsetService.Q (whitelist check at 0x2277b4)
# In orig:
# 2277b4: 7010 dd39 0400 invoke-direct {v4}, Q0:()Z
# Replace with:
# 2277b4: const/4 v0, 1 (12 10)
# 2277b6: return v0    (0f 00)
# Fill remaining instructions up to 0x2277fa with NOPs (00 00)
q_orig = d[0x2277b4:0x2277fa]
assert q_orig.startswith(bytes.fromhex('7010dd390400'))
q_patch = bytearray(len(q_orig))
q_patch[0:4] = bytes.fromhex('12100f00') # const/4 v0, 1; return v0
d[0x2277b4:0x2277fa] = q_patch
print("1. Patched BluetoothHeadsetService.Q to always return true")

# 2. Patch BluetoothHeadsetService.U0 branch at 0x22830a
# In orig:
# 22830a: 3264 1300 if-eq v4, v6, 0x228330 (+0x0013)
# Replace with unconditional goto to 0x228330:
# 22830a: goto +0x13 (28 13)
# 22830c: nop        (00 00)
assert d[0x22830a:0x22830e] == bytes.fromhex('32641300')
d[0x22830a:0x22830e] = bytes.fromhex('28130000')
print("2. Patched U0 to unconditionally branch to 0x228330")

# 3. Patch BluetoothHeadsetService.U0 setup at 0x228330
# In orig:
# 228330: 1a0d 9664 const-string v13, "device is not saved"
# 228334: 7120 f711 d000 invoke-static {v0, v13}, Log.e
# 22833a: 0f02 return v2
# Replace with:
# 228330: const/16 v5, #10 (LHDC codec index!)  (13 05 0a 00)
# 228334: const/4 v6, #1   (HD audio enabled)    (12 16)
# 228336: const/4 v12, #0  (skip extra logic)    (12 0c)
# 228338: goto 0x228342    (goto +5 code units)  (28 05)
# 22833a: nop                                    (00 00)
assert d[0x228330:0x22833c] == bytes.fromhex('1a0d96647120f711d0000f02')
d[0x228330:0x22833c] = bytes.fromhex('13050a001216120c28050000')
print("3. Patched U0 to load codec 10 (LHDC) with const/16 and jump to setCodec")

# 4. Patch BluetoothHeadsetService.U0 isOptionalCodecsEnabled check at 0x22841c
# In orig:
# 22841c: 33b3 0d00 if-ne v3, v11, 0x228436
# Replace with:
# 22841c: nop; nop (00 00 00 00)
assert d[0x22841c:0x228420] == bytes.fromhex('33b30d00')
d[0x22841c:0x228420] = bytes.fromhex('00000000')
print("4. Patched U0 to NOP isOptionalCodecsEnabled branch")

# 5. Recalculate Checksums
# SHA-1 covers offset 0x20 to EOF
sha1 = hashlib.sha1(d[0x20:]).digest()
d[0x0c:0x20] = sha1

# Adler-32 covers offset 0x0c to EOF
adler = zlib.adler32(d[0x0c:]) & 0xffffffff
d[0x08:0x0c] = struct.pack('<I', adler)

with open('classes_patched.dex', 'wb') as f:
    f.write(d)

print(f"Checksums updated: SHA1={sha1.hex()}, Adler32={hex(adler)}")
print("Successfully generated clean classes_patched.dex!")
