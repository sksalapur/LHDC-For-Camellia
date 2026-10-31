import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

string_ids_off = struct.unpack_from('<I', dex, 0x3c)[0]
method_ids_off = struct.unpack_from('<I', dex, 0x5c)[0]
type_ids_off = struct.unpack_from('<I', dex, 0x44)[0]

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

# Find any method containing 'Codec' or 'codec'
method_ids_size = struct.unpack_from('<I', dex, 0x58)[0]
for mid in range(method_ids_size):
    n = get_name(mid)
    if 'Codec' in n or 'codec' in n:
        class_idx = struct.unpack_from('<H', dex, method_ids_off + mid*8)[0]
        cname = get_type(class_idx)
        if 'Headset' in cname or 'headset' in cname or 'Bluetooth' in cname:
            print(f'Method {hex(mid)}: {cname}->{n}')
