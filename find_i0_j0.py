import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

method_ids_off = struct.unpack_from('<I', dex, 0x5c)[0]
string_ids_off = struct.unpack_from('<I', dex, 0x3c)[0]

def get_str(idx):
    off = struct.unpack_from('<I', dex, string_ids_off + idx*4)[0]
    p = off; l = 0; s = 0
    while True:
        b = dex[p]; p += 1
        l |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return dex[p:p+l].decode('utf-8', errors='ignore')

def get_name(mid):
    name_idx = struct.unpack_from('<I', dex, method_ids_off + mid*8 + 4)[0]
    return get_str(name_idx)

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
    if get_name(mid) == 'i0': print(f'Direct i0: mid={hex(mid)}, code_off={hex(c)}')
    if get_name(mid) == 'j0': print(f'Direct j0: mid={hex(mid)}, code_off={hex(c)}')

mid = 0
for _ in range(vms):
    d, p = read_uleb128(p); mid += d
    f, p = read_uleb128(p); c, p = read_uleb128(p)
    if get_name(mid) == 'i0': print(f'Virtual i0: mid={hex(mid)}, code_off={hex(c)}')
    if get_name(mid) == 'j0': print(f'Virtual j0: mid={hex(mid)}, code_off={hex(c)}')
