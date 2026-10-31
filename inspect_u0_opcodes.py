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

code_off = 0x2282e0
code = d[code_off:code_off+0x60]
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
    elif op == 0x0a:
        desc = f'move-result v{code[p+1]}'
        sz = 2
    elif op == 0x01:
        desc = f'move v{code[p+1]&0xf}, v{code[p+1]>>4}'
        sz = 2
    elif op == 0x12:
        desc = f'const/4 v{code[p+1]&0xf}, {code[p+1]>>4}'
        sz = 2
    elif op == 0x32:
        off = struct.unpack('<h', code[p+2:p+4])[0]
        desc = f'if-eq v{code[p+1]&0xf}, v{code[p+1]>>4}, {hex(code_off+p+off*2)}'
        sz = 4
    elif op == 0x38:
        off = struct.unpack('<h', code[p+2:p+4])[0]
        desc = f'if-eqz v{code[p+1]}, {hex(code_off+p+off*2)}'
        sz = 4
    elif op == 0x28:
        off = struct.unpack('<b', code[p+1:p+2])[0]
        desc = f'goto {hex(code_off+p+off*2)}'
        sz = 2
    print(f'{hex(code_off+p)}: {code[p:p+sz].hex():<10} {desc}')
    p += sz
