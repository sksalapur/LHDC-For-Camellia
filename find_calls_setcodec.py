import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

target = b'\xa6\x0b'
p = 0
while True:
    pos = dex.find(target, p)
    if pos == -1: break
    if pos > 1 and dex[pos-2] in (0x6e, 0x74): # invoke-virtual or invoke-virtual/range
        print(f'Found call to setCodecConfigPreference at {hex(pos-2)}')
    p = pos + 1
