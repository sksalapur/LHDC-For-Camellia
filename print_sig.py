import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

method_ids_off = struct.unpack_from('<I', dex, 0x5c)[0]
proto_ids_off = struct.unpack_from('<I', dex, 0x4c)[0]
string_ids_off = struct.unpack_from('<I', dex, 0x3c)[0]
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

for mid in [0x3a1a, 0x3a1c]:
    class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', dex, method_ids_off + mid * 8)
    shorty_idx, return_type_idx, parameters_off = struct.unpack_from('<III', dex, proto_ids_off + proto_idx * 12)
    params = []
    if parameters_off != 0:
        param_size = struct.unpack_from('<I', dex, parameters_off)[0]
        for i in range(param_size):
            t_idx = struct.unpack_from('<H', dex, parameters_off + 4 + i*2)[0]
            params.append(get_type(t_idx))
    print(f'{get_str(name_idx)}({", ".join(params)}) -> {get_type(return_type_idx)}')
