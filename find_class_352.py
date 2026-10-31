import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

string_ids_off = struct.unpack_from('<I', dex, 0x3c)[0]
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

# Find code_item covering 0x352cf2
# We search class_defs
class_defs_size, class_defs_off = struct.unpack_from('<II', dex, 0x60)
for i in range(class_defs_size):
    c_off = class_defs_off + i * 32
    cdata_off = struct.unpack_from('<I', dex, c_off + 24)[0]
    if cdata_off == 0: continue
    # Search methods in this class
    # We can check class name
    cname = get_type(struct.unpack_from('<I', dex, c_off)[0])
    # check if 0x352cf2 is in range of this class
"
