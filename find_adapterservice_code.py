import zipfile, struct

with zipfile.ZipFile('Bluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

# Find AdapterService class_def
class_defs_size, class_defs_off = struct.unpack_from('<II', dex, 0x60)
type_ids_off = struct.unpack_from('<I', dex, 0x44)[0]
string_ids_off = struct.unpack_from('<I', dex, 0x3c)[0]
method_ids_off = struct.unpack_from('<I', dex, 0x5c)[0]

def get_str(idx):
    off = struct.unpack_from('<I', dex, string_ids_off + idx*4)[0]
    p = off; l = 0; s = 0
    while True:
        b = dex[p]; p += 1
        l |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return dex[p:p+l].decode('utf-8', errors='ignore')

def get_type(idx):
    return get_str(struct.unpack_from('<I', dex, type_ids_off + idx*4)[0])

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

target = 'Lcom/android/bluetooth/btservice/AdapterService;'
for i in range(class_defs_size):
    c_off = class_defs_off + i * 32
    if get_type(struct.unpack_from('<I', dex, c_off)[0]) == target:
        cdata_off = struct.unpack_from('<I', dex, c_off + 24)[0]
        p = cdata_off
        sfs, p = read_uleb128(p); ifs, p = read_uleb128(p); dms, p = read_uleb128(p); vms, p = read_uleb128(p)
        for _ in range(sfs*2 + ifs*2): read_uleb128(p)
        mid = 0
        for _ in range(dms):
            d, p = read_uleb128(p); mid += d
            f, p = read_uleb128(p); c, p = read_uleb128(p)
            if mid == 0x40e7: print('Direct getSpecificCodecStatus code_off:', hex(c))
        mid = 0
        for _ in range(vms):
            d, p = read_uleb128(p); mid += d
            f, p = read_uleb128(p); c, p = read_uleb128(p)
            if mid == 0x40e7: print('Virtual getSpecificCodecStatus code_off:', hex(c))
        break
