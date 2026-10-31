import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    d = z.read('classes.dex')

string_ids_off = struct.unpack('<I', d[60:64])[0]
method_ids_off = struct.unpack('<I', d[92:96])[0]
type_ids_off = struct.unpack('<I', d[68:72])[0]
field_ids_off = struct.unpack('<I', d[84:88])[0]

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
registers_size, ins_size, outs_size, tries_size, debug_info_off, insns_size = struct.unpack('<HHHHII', d[code_off:code_off+16])
print(f'registers: {registers_size}, ins_size: {ins_size}, outs_size: {outs_size}, insns_size: {insns_size}')

insns = d[code_off+16:code_off+16+insns_size*2]

p = 0
while p < len(insns):
    op = insns[p]
    desc = f'{op:#04x}'
    sz = 2
    if op == 0x1a: # const-string
        reg = insns[p+1]
        sid = struct.unpack('<H', insns[p+2:p+4])[0]
        desc = f'const-string v{reg}, "{get_str(sid)}"'
        sz = 4
    elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
        mid = struct.unpack('<H', insns[p+2:p+4])[0]
        vC = insns[p+4] & 0xf
        vD = insns[p+4] >> 4
        mtype = {0x6e:'invoke-virtual', 0x6f:'invoke-super', 0x70:'invoke-direct', 0x71:'invoke-static', 0x72:'invoke-interface'}[op]
        desc = f'{mtype} {{v{vC}, v{vD}...}}, {get_method(mid)}'
        sz = 6
    elif op in (0x74, 0x75, 0x76):
        mid = struct.unpack('<H', insns[p+2:p+4])[0]
        vA = insns[p+1]
        vC = insns[p+4] | (insns[p+5] << 8)
        desc = f'invoke-range {{v{vC}..v{vC+vA-1}}}, {get_method(mid)}'
        sz = 6
    elif op == 0x01:
        desc = f'move v{insns[p+1]&0xf}, v{insns[p+1]>>4}'
        sz = 2
    elif op == 0x02:
        desc = f'move/from16 v{insns[p+1]}, v{struct.unpack("<H", insns[p+2:p+4])[0]}'
        sz = 4
    elif op == 0x07:
        desc = f'move-object v{insns[p+1]&0xf}, v{insns[p+1]>>4}'
        sz = 2
    elif op == 0x0a:
        desc = f'move-result v{insns[p+1]}'
        sz = 2
    elif op == 0x0c:
        desc = f'move-result-object v{insns[p+1]}'
        sz = 2
    elif op == 0x0e:
        desc = 'return-void'
        sz = 2
    elif op == 0x0f:
        desc = f'return v{insns[p+1]}'
        sz = 2
    elif op == 0x11:
        desc = f'return-object v{insns[p+1]}'
        sz = 2
    elif op == 0x12:
        desc = f'const/4 v{insns[p+1]&0xf}, {insns[p+1]>>4}'
        sz = 2
    elif op == 0x13:
        desc = f'const/16 v{insns[p+1]}, {struct.unpack("<h", insns[p+2:p+4])[0]}'
        sz = 4
    elif op == 0x22:
        cid = struct.unpack('<H', insns[p+2:p+4])[0]
        desc = f'new-instance v{insns[p+1]}, {get_type(cid)}'
        sz = 4
    elif op == 0x28:
        off = struct.unpack('<b', insns[p+1:p+2])[0]
        desc = f'goto {p + off*2:#06x}'
        sz = 2
    elif op == 0x32:
        off = struct.unpack('<h', insns[p+2:p+4])[0]
        desc = f'if-eq v{insns[p+1]&0xf}, v{insns[p+1]>>4}, {p + off*2:#06x}'
        sz = 4
    elif op == 0x33:
        off = struct.unpack('<h', insns[p+2:p+4])[0]
        desc = f'if-ne v{insns[p+1]&0xf}, v{insns[p+1]>>4}, {p + off*2:#06x}'
        sz = 4
    elif op == 0x38:
        off = struct.unpack('<h', insns[p+2:p+4])[0]
        desc = f'if-eqz v{insns[p+1]}, {p + off*2:#06x}'
        sz = 4
    elif op == 0x39:
        off = struct.unpack('<h', insns[p+2:p+4])[0]
        desc = f'if-nez v{insns[p+1]}, {p + off*2:#06x}'
        sz = 4
    elif op in (0x54, 0x5b):
        sz = 4
        desc = f'iget/iput'
    raw_bytes = insns[p:p+sz].hex()
    print(f'{code_off+16+p:#08x} (0x{p:04x}): {raw_bytes:<12} {desc}')
    p += sz
