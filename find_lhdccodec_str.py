import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

string_ids_size, string_ids_off = struct.unpack_from('<II', dex, 0x38)

for i in range(string_ids_size):
    off = struct.unpack_from('<I', dex, string_ids_off + i*4)[0]
    if dex[off:off+20].find(b'LHDCCodec') != -1:
        print(f'Found string_id={i} ({hex(i)})')
        sid = i
        break

# find const-string
sid_bytes = struct.pack('<H', sid)
p = 0
while True:
    pos = dex.find(sid_bytes, p)
    if pos == -1: break
    if pos > 1 and dex[pos-2] == 0x1a:
        print(f'const-string at {hex(pos-2)}')
    p = pos + 1
