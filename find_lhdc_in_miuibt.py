import zipfile

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    dex = z.read('classes.dex')

pos = 0
while True:
    p = dex.find(b'LHDC', pos)
    if p == -1: break
    print(f'Found LHDC at {hex(p)}: {dex[p:p+30]}')
    pos = p + 1
