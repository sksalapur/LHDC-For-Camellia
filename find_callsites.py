import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    d = z.read('classes.dex')

string_ids_off = struct.unpack('<I', d[60:64])[0]
method_ids_off = struct.unpack('<I', d[92:96])[0]
type_ids_off = struct.unpack('<I', d[68:72])[0]

def get_str(idx):
    off = struct.unpack('<I', d[string_ids_off + idx*4 : string_ids_off + (idx+1)*4])[0]
    p = off
    while d[p] & 0x80: p += 1
    p += 1
    return d[p:d.find(b'\x00', p)].decode('utf-8', 'ignore')

def get_type(idx):
    s_idx = struct.unpack('<I', d[type_ids_off + idx*4 : type_ids_off + (idx+1)*4])[0]
    return get_str(s_idx)

def get_method(idx):
    c_idx, p_idx, n_idx = struct.unpack('<HHI', d[method_ids_off + idx*8 : method_ids_off + (idx+1)*8])
    return f'{get_type(c_idx)}->{get_str(n_idx)}'

p = 0x22c700
while p < 0x22c780:
    op = d[p]
    if op in (0x1a, 0x1b):
        sid = struct.unpack('<H', d[p+2:p+4])[0]
        print(f'0x{p:x}: const-string "{get_str(sid)}"')
        p += 4
    elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
        mid = struct.unpack('<H', d[p+2:p+4])[0]
        print(f'0x{p:x}: invoke {get_method(mid)}')
        p += 6
    else:
        p += 2
