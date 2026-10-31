import zipfile, struct

with zipfile.ZipFile('MiuiBluetooth.apk', 'r') as z:
    d = z.read('classes.dex')

string_ids_off = struct.unpack('<I', d[60:64])[0]
method_ids_off = struct.unpack('<I', d[92:96])[0]
type_ids_off = struct.unpack('<I', d[68:72])[0]
class_defs_off = struct.unpack('<I', d[100:104])[0]
class_defs_size = struct.unpack('<I', d[96:100])[0]

def get_str(idx):
    off = struct.unpack('<I', d[string_ids_off + idx*4 : string_ids_off + (idx+1)*4])[0]
    p = off
    while d[p] & 0x80: p += 1
    p += 1
    return d[p:d.find(b'\x00', p)].decode('utf-8', 'ignore')

def get_type(idx):
    s_idx = struct.unpack('<I', d[type_ids_off + idx*4 : type_ids_off + (idx+1)*4])[0]
    return get_str(s_idx)

def get_method(idx):
    c_idx, p_idx, n_idx = struct.unpack('<HHI', d[method_ids_off + idx*8 : method_ids_off + (idx+1)*8])
    return f'{get_type(c_idx)}->{get_str(n_idx)}'

def read_uleb128(data, off):
    val, shift = 0, 0
    while True:
        b = data[off]
        off += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return val, off

for i in range(class_defs_size):
    class_idx, aflags, super_idx, iface_off, src_idx, annot_off, class_data_off, static_val_off = struct.unpack('<IIIIIIII', d[class_defs_off + i*32 : class_defs_off + (i+1)*32])
    if class_data_off == 0: continue
    off = class_data_off
    sf, off = read_uleb128(d, off)
    inf, off = read_uleb128(d, off)
    dm, off = read_uleb128(d, off)
    vm, off = read_uleb128(d, off)
    for _ in range(sf + inf):
        _, off = read_uleb128(d, off)
        _, off = read_uleb128(d, off)
    cur_m = 0
    for _ in range(dm):
        diff, off = read_uleb128(d, off)
        m_flags, off = read_uleb128(d, off)
        c_off, off = read_uleb128(d, off)
        cur_m += diff
        if code_off <= 0x2336f6 < code_off + 16 + insns_size*2:
            print(f'Direct method at 0x228200: {get_method(cur_m)}')
    cur_m = 0
    for _ in range(vm):
        diff, off = read_uleb128(d, off)
        m_flags, off = read_uleb128(d, off)
        c_off, off = read_uleb128(d, off)
        cur_m += diff
        if code_off <= 0x2336f6 < code_off + 16 + insns_size*2:
            print(f'Virtual method at 0x228200: {get_method(cur_m)}')
