import zipfile, struct

with zipfile.ZipFile('miui_framework_bt.jar', 'r') as z:
    dex = z.read('classes.dex')

string_ids_off = struct.unpack_from('<I', dex, 0x3c)[0]
field_ids_off = struct.unpack_from('<I', dex, 0x54)[0]
type_ids_off = struct.unpack_from('<I', dex, 0x44)[0]
class_defs_off = struct.unpack_from('<I', dex, 0x60)[0]
class_defs_size = struct.unpack_from('<I', dex, 0x58)[0]

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

target = 'Landroid/bluetooth/BluetoothCodecConfig;'
for i in range(class_defs_size):
    c_off = class_defs_off + i * 32
    if get_type(struct.unpack_from('<I', dex, c_off)[0]) == target:
        static_values_off = struct.unpack_from('<I', dex, c_off + 28)[0]
        print('Found BluetoothCodecConfig class_def, static_values_off:', hex(static_values_off))
        # Let's search inside the class for references to 9, 10, 11
        break
