import zipfile, struct, re

with zipfile.ZipFile('timbre.apk', 'r') as z:
    d = z.read('classes.dex')

string_ids_off = struct.unpack('<I', d[60:64])[0]
type_ids_off = struct.unpack('<I', d[68:72])[0]

def get_str(idx):
    off = struct.unpack('<I', d[string_ids_off + idx*4 : string_ids_off + (idx+1)*4])[0]
    p = off
    while d[p] & 0x80: p += 1
    p += 1
    return d[p:d.find(b'\x00', p)].decode('utf-8', 'ignore')

# Find class def for LosslessOutput
class_defs_size = struct.unpack('<I', d[96:100])[0]
class_defs_off = struct.unpack('<I', d[100:104])[0]

for i in range(class_defs_size):
    class_idx, access_flags, superclass_idx, interfaces_off, source_file_idx, annotations_off, class_data_off, static_values_off = struct.unpack('<IIIIIIII', d[class_defs_off + i*32 : class_defs_off + (i+1)*32])
    cname = get_str(struct.unpack('<I', d[type_ids_off + class_idx*4 : type_ids_off + (class_idx+1)*4])[0])
    if 'LosslessOutput' in cname:
        print(f"Class: {cname} at class_data_off 0x{class_data_off:x}")
        # Search for code in this class
        # Let's inspect class data
        if class_data_off > 0:
            chunk = d[class_data_off:class_data_off+10000]
            # search for string references
            # let's look for all const-string opcodes
