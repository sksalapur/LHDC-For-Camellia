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
    return d[p:d.find(b'\0', p)].decode('utf-8', 'ignore')
def get_type(idx):
    return get_str(struct.unpack('<I', d[type_ids_off + idx*4 : type_ids_off + (idx+1)*4])[0])
def get_method(idx):
    c_idx, p_idx, n_idx = struct.unpack('<HHI', d[method_ids_off + idx*8 : method_ids_off + (idx+1)*8])
    return f'{get_type(c_idx)}->{get_str(n_idx)}'

for off in [0x2336e0, 0x237240, 0x2456b0]:
    print('--- Off:', hex(off))
    for p in range(off, off+40, 2):
        op = d[p]
        if op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
            mid = struct.unpack('<H', d[p+2:p+4])[0]
            print(f'  {hex(p)}: invoke {get_method(mid)}')
        elif op == 0x1a:
            sid = struct.unpack('<H', d[p+2:p+4])[0]
            print(f'  {hex(p)}: const-string "{get_str(sid)}"')
