import zipfile, struct

with zipfile.ZipFile('Bluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

string_ids_off = struct.unpack_from('<I', dex, 0x3c)[0]
field_ids_off = struct.unpack_from('<I', dex, 0x54)[0]
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

# Search for TRANSACTION_ in IBluetoothA2dp$Stub
pos = 0
while True:
    p = dex.find(b'TRANSACTION_', pos)
    if p == -1: break
    # print string
    s = dex[p:p+40].split(b'\0')[0].decode('utf-8', errors='ignore')
    if 'Codec' in s or 'Optional' in s:
        print(s)
    pos = p + 1
