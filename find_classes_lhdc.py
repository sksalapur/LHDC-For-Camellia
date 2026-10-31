import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    data = z.read('classes.dex')

string_ids_size = struct.unpack('<I', data[56:60])[0]
string_ids_off = struct.unpack('<I', data[60:64])[0]

target_idx = 12160
# Look for 0x1a (const-string) with 12160
p16 = struct.pack('<BH', 0x1a, target_idx)
pos = 0
found = []
while True:
    p = data.find(p16, pos)
    if p == -1: break
    found.append(p)
    pos = p + 3

print(f"Found {len(found)} references to string {target_idx} in classes.dex")
for p in found:
    print(f"Offset 0x{p:x}")
    # print context
    chunk = data[max(0, p-60):min(len(data), p+60)]
    print("  Bytes:", chunk.hex(' '))
