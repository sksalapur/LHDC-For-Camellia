import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    d = z.read('classes.dex')

method_ids_off = struct.unpack('<I', d[92:96])[0]
type_ids_off = struct.unpack('<I', d[68:72])[0]
string_ids_off = struct.unpack('<I', d[60:64])[0]

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
    class_idx, proto_idx, name_idx = struct.unpack('<HHI', d[method_ids_off + idx*8 : method_ids_off + (idx+1)*8])
    return f"{get_type(class_idx)}->{get_str(name_idx)}"

for i in range(0x7991a0, 0x799360, 2):
    op = d[i]
    if op == 0x1a:
        sid = struct.unpack('<H', d[i+2:i+4])[0]
        print(f"0x{i:x}: const-string \"{get_str(sid)}\"")
    elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
        mid = struct.unpack('<H', d[i+2:i+4])[0]
        print(f"0x{i:x}: invoke {get_method(mid)}")
