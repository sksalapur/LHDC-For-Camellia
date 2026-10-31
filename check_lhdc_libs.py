import subprocess

def check_symbols(path):
    print('Checking symbols in', path)
    with open(path, 'rb') as f:
        data = f.read()
    
    needed = [
        b'lhdcv5BT_get_handle',
        b'lhdcv5BT_free_handle',
        b'lhdcv5BT_get_bitrate',
        b'lhdcv5BT_set_bitrate',
        b'lhdcv5BT_set_max_bitrate',
        b'lhdcv5BT_set_min_bitrate',
        b'lhdcv5BT_adjust_bitrate',
        b'lhdcv5BT_init_encoder',
        b'lhdcv5BT_get_block_Size',
        b'lhdcv5BT_encode',
    ]
    for s in needed:
        print(s.decode(), '->', 'FOUND' if s in data else 'MISSING')

check_symbols('spr_liblhdc/AOSP/other_so_files/enc/LHDC-magisk-11_arm64/system/lib64/liblhdcv5BT_enc.so')
check_symbols('spr_liblhdc/AOSP/other_so_files/enc/LHDC-magisk-11_arm64/system/lib64/liblhdcBT_enc.so')
