with open('derp_patches/0_packages_modules_Bluetooth.patch', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

target = 'static const char* LHDC_ENCODER_LIB_NAME = "liblhdcv5BT_enc.so";'
pos = text.find(target)
if pos != -1:
    chunk = text[pos:pos+3000]
    for line in chunk.split('\n')[:70]:
        print(line)
