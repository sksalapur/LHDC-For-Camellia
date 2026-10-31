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

p = 0x228342
sub = dex[p:0x228438]
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
        vC = sub[i+4] & 0xf
        vD = sub[i+4] >> 4
        mtype = {0x6e:'invoke-virtual', 0x70:'invoke-direct', 0x71:'invoke-static', 0x72:'invoke-super'}[op]
        print(f'{hex(p+i)}: {mtype} {{v{vC}, v{vD}}}, {get_method(mid)}')
        i += 6
    elif op in (0x74, 0x76):
        mid = sub[i+2] | (sub[i+3] << 8)
        vC = sub[i+4]
        vA = sub[i+1]
        print(f'{hex(p+i)}: invoke-range {{v{vC}..v{vC+vA-1}}}, {get_method(mid)}')
        i += 6
    elif op == 0x0a:
        print(f'{hex(p+i)}: move-result v{sub[i+1]}')
        i += 2
    elif op == 0x0c:
        print(f'{hex(p+i)}: move-result-object v{sub[i+1]}')
        i += 2
    elif op == 0x38:
        offset = struct.unpack_from('<h', sub, i+2)[0]
        print(f'{hex(p+i)}: if-eqz v{sub[i+1]}, {hex(p+i+offset*2)}')
        i += 4
    elif op == 0x39:
        offset = struct.unpack_from('<h', sub, i+2)[0]
        print(f'{hex(p+i)}: if-nez v{sub[i+1]}, {hex(p+i+offset*2)}')
        i += 4
    elif op == 0x12:
        print(f'{hex(p+i)}: const/4 v{sub[i+1]&0xf}, {sub[i+1]>>4}')
        i += 2
    elif op == 0x22:
        cid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: new-instance v{sub[i+1]}, {get_type(cid)}')
        i += 4
    elif op == 0x28:
        offset = struct.unpack_from('<b', sub, i+1)[0]
        print(f'{hex(p+i)}: goto {hex(p+i + offset*2)}')
        i += 2
    elif op == 0x0f:
        print(f'{hex(p+i)}: return v{sub[i+1]}')
        i += 2
    elif op == 0x54:
        reg = sub[i+1] & 0xf
        obj = sub[i+1] >> 4
        fid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: iget-object v{reg}, v{obj}, field@{hex(fid)}')
        i += 4
    elif op == 0x5b:
        reg = sub[i+1] & 0xf
        obj = sub[i+1] >> 4
        fid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: iput-object v{reg}, v{obj}, field@{hex(fid)}')
        i += 4
    elif op == 0x62:
        reg = sub[i+1]
        fid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: sget-object v{reg}, field@{hex(fid)}')
        i += 4
    elif op == 0x01:
        print(f'{hex(p+i)}: move v{sub[i+1]&0xf}, v{sub[i+1]>>4}')
        i += 2
    else:
        print(f'{hex(p+i)}: opcode {hex(op)}')
        i += 2
