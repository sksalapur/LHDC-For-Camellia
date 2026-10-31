import zipfile, struct

with zipfile.ZipFile('miui_framework_bt.jar', 'r') as z:
    dex = z.read('classes.dex')

string_ids_size, string_ids_off = struct.unpack('<II', dex[0x38:0x40])
def get_string(idx):
    off = struct.unpack('<I', dex[string_ids_off + idx*4 : string_ids_off + (idx+1)*4])[0]
    p = off; l = 0; shift = 0
    while True:
        val = dex[p]; p += 1; l |= (val & 0x7f) << shift
        if not (val & 0x80): break
        shift += 7
    return dex[p:p+l].decode('utf-8', 'ignore')

p = 0x36e88
regs, ins, outs, tries, debug_off, insns_size = struct.unpack('<HHHHII', dex[p:p+16])
insns = dex[p+16 : p+16 + insns_size*2]
print(f'insns_size: {insns_size}')

for i in range(0, len(insns), 2):
    op = insns[i]
    if op in (0x1a, 0x1b):
        str_idx = struct.unpack('<H', insns[i+2:i+4])[0]
        print(f'  [{i//2}] const-string {get_string(str_idx)}')
    elif op == 0x2b or op == 0x2c:
        offset = struct.unpack('<i', insns[i+2:i+6])[0]
        switch_addr = (i // 2) + offset
        print(f'  [{i//2}] switch payload at instruction {switch_addr}')
        sp_off = p + 16 + switch_addr*2
        ident, size = struct.unpack('<HH', dex[sp_off:sp_off+4])
        print(f'    switch ident={hex(ident)}, size={size}')
        if ident == 0x0100: # packed-switch
            first_key = struct.unpack('<i', dex[sp_off+4:sp_off+8])[0]
            print(f'    first_key={first_key}')
            targets = struct.unpack(f'<{size}i', dex[sp_off+8 : sp_off+8+size*4])
            for k, tgt in enumerate(targets):
                print(f'      case {first_key + k} -> target {(i//2) + tgt}')
        elif ident == 0x0200: # sparse-switch
            keys = struct.unpack(f'<{size}i', dex[sp_off+4 : sp_off+4+size*4])
            targets = struct.unpack(f'<{size}i', dex[sp_off+4+size*4 : sp_off+4+size*8])
            for k, tgt in zip(keys, targets):
                print(f'      case {k} -> target {(i//2) + tgt}')
