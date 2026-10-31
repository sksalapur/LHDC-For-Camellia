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

for i in range(0x799050, 0x799380, 2):
    op = d[i]
    if op == 0x1a:
        sid = struct.unpack('<H', d[i+2:i+4])[0]
        s = get_str(sid)
        print(f"0x{i:x}: const-string \"{s}\"")
