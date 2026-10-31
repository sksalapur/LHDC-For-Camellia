import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    d = z.read('classes.dex')

string_ids_size = struct.unpack('<I', d[56:60])[0]
string_ids_off = struct.unpack('<I', d[60:64])[0]

def get_str(idx):
    if idx >= string_ids_size: return f"<invalid id {idx}>"
    off = struct.unpack('<I', d[string_ids_off + idx*4 : string_ids_off + (idx+1)*4])[0]
    p = off
    while d[p] & 0x80: p += 1
    p += 1
    return d[p:d.find(b'\x00', p)].decode('utf-8', 'ignore')

# Dump hex and simple disassembly around 0x799070 to 0x799220
i = 0x799070
while i < 0x799220:
    op = d[i]
    if op == 0x1a: # const-string
        reg = d[i+1]
        sid = struct.unpack('<H', d[i+2:i+4])[0]
        print(f"0x{i:x}: const-string v{reg}, \"{get_str(sid)}\"")
        i += 4
    elif op == 0x12: # const/4
        reg = d[i+1] & 0x0f
        val = (d[i+1] >> 4)
        print(f"0x{i:x}: const/4 v{reg}, {val}")
        i += 2
    elif op == 0x13: # const/16
        reg = d[i+1]
        val = struct.unpack('<h', d[i+2:i+4])[0]
        print(f"0x{i:x}: const/16 v{reg}, {val}")
        i += 4
    elif op in (0x32, 0x33, 0x34, 0x35, 0x36, 0x37): # if-test
        print(f"0x{i:x}: if-test v{d[i+1]&0xf}, v{d[i+1]>>4}, target=0x{i + struct.unpack('<h', d[i+2:i+4])[0]*2:x}")
        i += 4
    elif op in (0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d): # if-testz
        print(f"0x{i:x}: if-testz v{d[i+1]}, target=0x{i + struct.unpack('<h', d[i+2:i+4])[0]*2:x}")
        i += 4
    elif op == 0x28: # goto
        print(f"0x{i:x}: goto 0x{i + struct.unpack('<b', bytes([d[i+1]]))[0]*2:x}")
        i += 2
    elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72): # invoke
        print(f"0x{i:x}: invoke kind=0x{op:x} method_id={struct.unpack('<H', d[i+2:i+4])[0]}")
        i += 6
    else:
        i += 2
