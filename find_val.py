import zipfile

with zipfile.ZipFile('miui_framework_bt.jar', 'r') as z:
    dex = z.read('classes.dex')

# In dex, static final int fields often have values in encoded_array in class_def
# Let's find class_def for BluetoothCodecConfig
# Or search bytecode where SOURCE_CODEC_TYPE_LHDCV3 is assigned
pos = dex.find(b'SOURCE_CODEC_TYPE_LHDCV3')
print('Found at', hex(pos))
