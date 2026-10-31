import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    d = z.read('classes.dex')

string_ids_off = struct.unpack('<I', d[60:64])[0]
type_ids_off = struct.unpack('<I', d[68:72])[0]
method_ids_off = struct.unpack('<I', d[92:96])[0]

def get_str(idx):
    off = struct.unpack('<I', d[string_ids_off + idx*4 : string_ids_off + (idx+1)*4])[0]
    p = off
    while d[p] & 0x80: p += 1
    p += 1
    return d[p:d.find(b'\x00', p)].decode('utf-8', 'ignore')

def read_uleb128(data, off):
    val, shift = 0, 0
    while True:
        b = data[off]
        off += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return val, off

# Find class def for Regex$Companion
class_defs_size = struct.unpack('<I', d[96:100])[0]
class_defs_off = struct.unpack('<I', d[100:104])[0]

for i in range(class_defs_size):
    class_idx, access_flags, superclass_idx, interfaces_off, source_file_idx, annotations_off, class_data_off, static_values_off = struct.unpack('<IIIIIIII', d[class_defs_off + i*32 : class_defs_off + (i+1)*32])
    # check type
    s_idx = struct.unpack('<I', d[type_ids_off + class_idx*4 : type_ids_off + (class_idx+1)*4])[0]
    if get_str(s_idx) == 'Lkotlin/text/Regex$Companion;':
        print(f"Found Regex$Companion at class_data_off 0x{class_data_off:x}")
        off = class_data_off
        static_f, off = read_uleb128(d, off)
        inst_f, off = read_uleb128(d, off)
        dir_m, off = read_uleb128(d, off)
        virt_m, off = read_uleb128(d, off)
        for _ in range(static_f + inst_f):
            _, off = read_uleb128(d, off)
            _, off = read_uleb128(d, off)
        m_idx = 0
        for _ in range(dir_m + virt_m):
            diff, off = read_uleb128(d, off)
            aflags, off = read_uleb128(d, off)
            code_off, off = read_uleb128(d, off)
            m_idx += diff
            if m_idx == 63370:
                print(f"Found mapCodecType code_off: 0x{code_off:x}")
                insns_size = struct.unpack('<I', d[code_off+12:code_off+16])[0]
                insns = d[code_off+16:code_off+16+insns_size*2]
                print("Code bytes len:", len(insns))
                for j in range(0, len(insns), 2):
                    op = insns[j]
                    if op == 0x1a:
                        sid = struct.unpack('<H', insns[j+2:j+4])[0]
                        print(f"  0x{j:x}: const-string \"{get_str(sid)}\"")
                    elif op == 0x13:
                        val = struct.unpack('<h', insns[j+2:j+4])[0]
                        print(f"  0x{j:x}: const/16 {val}")
                    elif op in (0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d):
                        print(f"  0x{j:x}: if-branch op=0x{op:x}")
                    elif op in (0x2b, 0x2c):
                        print(f"  0x{j:x}: switch op=0x{op:x}")
