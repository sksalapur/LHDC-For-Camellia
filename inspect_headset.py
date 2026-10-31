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

code_off = 0x228200
insns_size = struct.unpack('<I', d[code_off+12:code_off+16])[0]
insns = d[code_off+16:code_off+16+insns_size*2]

p = 0
while p < len(insns):
    op = insns[p]
    line = f'0x{p:04x}: {hex(op)}'
    if op == 0x1a:
        sid = struct.unpack('<H', insns[p+2:p+4])[0]
        line += f' const-string "{get_str(sid)}"'
        p += 4
    elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
        mid = struct.unpack('<H', insns[p+2:p+4])[0]
        line += f' invoke {get_method(mid)}'
        p += 6
    else:
        p += 2
    if any(k in line.lower() for k in ['codec', 'device', 'allow', 'headset', 'enter']):
        print(line)
