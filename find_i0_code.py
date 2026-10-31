import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

method_ids_off = struct.unpack_from('<I', dex, 0x5c)[0]

# Method 0x3a1a is i0
# Let's find its code_off from method_id 0x3a1a
# We know BluetoothHeadsetService class_data_off = 0x5c12a1
def read_uleb128(p):
    val = 0; shift = 0
    while True:
        b = dex[p]; p += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return val, p

p = 0x5c12a1
sfs, p = read_uleb128(p); ifs, p = read_uleb128(p); dms, p = read_uleb128(p); vms, p = read_uleb128(p)
for _ in range(sfs): read_uleb128(p); read_uleb128(p)
for _ in range(ifs): read_uleb128(p); read_uleb128(p)

mid = 0
for _ in range(dms):
    d, p = read_uleb128(p); mid += d
    f, p = read_uleb128(p); c, p = read_uleb128(p)
    if mid == 0x3a1a: print('Direct i0 code_off:', hex(c))

mid = 0
for _ in range(vms):
    d, p = read_uleb128(p); mid += d
    f, p = read_uleb128(p); c, p = read_uleb128(p)
    if mid == 0x3a1a: print('Virtual i0 code_off:', hex(c))
