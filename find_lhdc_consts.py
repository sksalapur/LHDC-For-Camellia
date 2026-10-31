import zipfile, struct

with zipfile.ZipFile('miui_framework_bt.jar', 'r') as z:
    dex = z.read('classes.dex')

string_ids_off = struct.unpack_from('<I', dex, 0x3c)[0]
field_ids_off = struct.unpack_from('<I', dex, 0x54)[0]
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

field_ids_size = struct.unpack_from('<I', dex, 0x50)[0]
for fid in range(field_ids_size):
    class_idx, type_idx, name_idx = struct.unpack_from('<HHI', dex, field_ids_off + fid*8)
    name = get_str(name_idx)
    if 'LHDC' in name:
        print(f'{get_type(class_idx)}->{name} : {get_type(type_idx)}')
