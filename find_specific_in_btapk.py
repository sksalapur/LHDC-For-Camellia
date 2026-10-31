import zipfile, struct

with zipfile.ZipFile('Bluetooth.apk', 'r') as z:
    for name in z.namelist():
        if name.endswith('.dex'):
            dex = z.read(name)
            p = dex.find(b'getSpecificCodecStatus')
            if p != -1:
                print(f'Found getSpecificCodecStatus in {name} at {hex(p)}')
