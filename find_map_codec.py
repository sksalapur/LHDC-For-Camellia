import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    d = z.read('classes.dex')

string_ids_off = struct.unpack('<I', d[60:64])[0]
type_ids_off = struct.unpack('<I', d[68:72])[0]
method_ids_off = struct.unpack('<I', d[92:96])[0]

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

# find method mapCodecType
method_ids_size = struct.unpack('<I', d[88:92])[0]
for i in range(method_ids_size):
    class_idx, proto_idx, name_idx = struct.unpack('<HHI', d[method_ids_off + i*8 : method_ids_off + (i+1)*8])
    if get_str(name_idx) == 'mapCodecType':
        print(f"mapCodecType at method_id {i} in class {get_type(class_idx)}")
