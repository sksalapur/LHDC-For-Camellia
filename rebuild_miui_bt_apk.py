import zipfile, os

with open('classes_patched.dex', 'rb') as f:
    patched_dex = f.read()

src_apk = 'MiuiBluetooth.apk'
out_apk = 'MiuiBluetooth_patched.apk'

with zipfile.ZipFile(src_apk, 'r') as zin, zipfile.ZipFile(out_apk + '.tmp', 'w', compression=zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename == 'classes.dex':
            # Write uncompressed or deflated depending on original (usually deflated or stored)
            zout.writestr(item, patched_dex)
            print(f"Replaced {item.filename} with patched dex ({len(patched_dex)} bytes)")
        else:
            zout.writestr(item, zin.read(item.filename))

if os.path.exists(out_apk):
    os.remove(out_apk)
os.rename(out_apk + '.tmp', out_apk)
print(f"Successfully rebuilt {out_apk}!")
