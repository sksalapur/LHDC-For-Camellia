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

def get_method(idx):
    m_off = method_ids_off + idx * 8
    class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', dex, m_off)
    return f'{get_type(class_idx)}->{get_str(name_idx)}'

p = 0x1fc350
sub = dex[p:p+100]
i = 0
while i < len(sub):
    op = sub[i]
    if op == 0x1a:
        reg = sub[i+1]
        sid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: const-string v{reg}, "{get_str(sid)}"')
        i += 4
    elif op in (0x6e, 0x70, 0x71, 0x72):
        mid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: invoke {get_method(mid)}')
        i += 6
    elif op == 0x0a:
        print(f'{hex(p+i)}: move-result v{sub[i+1]}')
        i += 2
    elif op == 0x0c:
        print(f'{hex(p+i)}: move-result-object v{sub[i+1]}')
        i += 2
    else:
        print(f'{hex(p+i)}: opcode {hex(op)}')
        i += 2
