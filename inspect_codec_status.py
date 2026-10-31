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

for base in [0x133950, 0x353430]:
    print('--- Disassembling from', hex(base), '---')
    code = d[base:base+100]
    p = 0
    while p < len(code):
        op = code[p]
        desc = hex(op)
        sz = 2
        if op == 0x1a:
            sid = struct.unpack('<H', code[p+2:p+4])[0]
            desc = f'const-string v{code[p+1]}, "{get_str(sid)}"'
            sz = 4
        elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
            mid = struct.unpack('<H', code[p+2:p+4])[0]
            desc = f'invoke {get_method(mid)}'
            sz = 6
        print(f'{hex(base+p)}: {desc}')
        p += sz
