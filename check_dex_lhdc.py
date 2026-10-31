import zipfile

with zipfile.ZipFile('miui_framework_bt.jar', 'r') as z:
    for name in z.namelist():
        if name.endswith('.dex'):
            data = z.read(name)
            # Find SOURCE_CODEC_TYPE_LHDCV
            pos = 0
            while True:
                p = data.find(b'SOURCE_CODEC_TYPE_LHDC', pos)
                if p == -1: break
                print(data[p:p+30])
                pos = p + 20
