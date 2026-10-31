import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    data = z.read('classes2.dex')

string_ids_size = struct.unpack('<I', data[56:60])[0]
string_ids_off = struct.unpack('<I', data[60:64])[0]

def get_str(idx):
    if idx >= string_ids_size: return f'<id:{idx}>'
    str_data_off = struct.unpack('<I', data[string_ids_off + idx*4 : string_ids_off + (idx+1)*4])[0]
    p = str_data_off
    while data[p] & 0x80: p += 1
    p += 1
    end = data.find(b'\x00', p)
    return data[p:end].decode('utf-8', 'ignore')

for i in range(0x546e00, 0x547050, 2):
    if data[i] == 0x1a:
        str_id = struct.unpack('<H', data[i+2:i+4])[0]
        print(f"0x{i:x}: const-string v{data[i+1]}, \"{get_str(str_id)}\"")
