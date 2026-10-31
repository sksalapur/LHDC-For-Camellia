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
sub = dex[p:p+200]
i = 0
while i < len(sub):
    op = sub[i]
    if op == 0x1a:
        reg = sub[i+1]
        sid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: const-string v{reg}, "{get_str(sid)}"')
        i += 4
    elif op == 0x6e:
        mid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: invoke-virtual {get_method(mid)}')
        i += 6
    elif op == 0x71:
        mid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: invoke-static {get_method(mid)}')
        i += 6
    elif op == 0x70:
        mid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: invoke-direct {get_method(mid)}')
        i += 6
    elif op == 0x72:
        mid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: invoke-super {get_method(mid)}')
        i += 6
    elif op == 0x74: # invoke-virtual/range
        mid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: invoke-virtual/range {get_method(mid)}')
        i += 6
    elif op == 0x76: # invoke-static/range
        mid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: invoke-static/range {get_method(mid)}')
        i += 6
    elif op == 0x0a:
        reg = sub[i+1]
        print(f'{hex(p+i)}: move-result v{reg}')
        i += 2
    elif op == 0x0c:
        reg = sub[i+1]
        print(f'{hex(p+i)}: move-result-object v{reg}')
        i += 2
    elif op == 0x38:
        print(f'{hex(p+i)}: if-eqz v{sub[i+1]}, +{sub[i+2]|(sub[i+3]<<8)}')
        i += 4
    elif op == 0x39:
        print(f'{hex(p+i)}: if-nez v{sub[i+1]}, +{sub[i+2]|(sub[i+3]<<8)}')
        i += 4
    elif op == 0x12:
        print(f'{hex(p+i)}: const/4 v{sub[i+1]&0xf}, {sub[i+1]>>4}')
        i += 2
    elif op == 0x22:
        cid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: new-instance v{sub[i+1]}, {get_type(cid)}')
        i += 4
    elif op == 0x62: # sget-object
        fid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: sget-object v{sub[i+1]}, field@{hex(fid)}')
        i += 4
    elif op == 0x54: # iget-object
        fid = sub[i+2] | (sub[i+3] << 8)
        print(f'{hex(p+i)}: iget-object v{sub[i+1]}, field@{hex(fid)}')
        i += 4
    else:
        print(f'{hex(p+i)}: opcode {hex(op)}')
        i += 2
