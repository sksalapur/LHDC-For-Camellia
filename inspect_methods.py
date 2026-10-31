import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    d = z.read('classes.dex')

string_ids_off = struct.unpack('<I', d[60:64])[0]
type_ids_off = struct.unpack('<I', d[68:72])[0]
method_ids_off = struct.unpack('<I', d[88:92])[0]

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
    class_idx, proto_idx, name_idx = struct.unpack('<HHI', d[method_ids_off + idx*8 : method_ids_off + (idx+1)*8])
    return f"{get_type(class_idx)}->{get_str(name_idx)}"

def read_uleb128(data, off):
    val = 0
    shift = 0
    while True:
        b = data[off]
        off += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return val, off

# parse LosslessOutput class_data at 0xa801f7
off = 0xa801f7
static_fields, off = read_uleb128(d, off)
instance_fields, off = read_uleb128(d, off)
direct_methods, off = read_uleb128(d, off)
virtual_methods, off = read_uleb128(d, off)

# skip fields
for _ in range(static_fields + instance_fields):
    _, off = read_uleb128(d, off)
    _, off = read_uleb128(d, off)

methods = []
m_idx = 0
for _ in range(direct_methods + virtual_methods):
    diff, off = read_uleb128(d, off)
    access_flags, off = read_uleb128(d, off)
    code_off, off = read_uleb128(d, off)
    m_idx += diff
    methods.append((m_idx, code_off))

for mid, coff in methods:
    mname = get_method(mid)
    print(f"Method: {mname} at code_off 0x{coff:x}")
    if coff > 0:
        insns_size = struct.unpack('<I', d[coff+12:coff+16])[0]
        insns = d[coff+16:coff+16+insns_size*2]
        # scan for const-string or invoke
        # let's find strings in this method
        for i in range(0, len(insns)-2, 2):
            op = insns[i]
            if op == 0x1a:
                s_idx = struct.unpack('<H', insns[i+2:i+4])[0]
                print(f"    const-string \"{get_str(s_idx)}\"")
            elif op == 0x1b:
                s_idx = struct.unpack('<I', insns[i+2:i+6])[0]
                print(f"    const-string/jumbo \"{get_str(s_idx)}\"")
            elif op in (0x6e, 0x6f, 0x70, 0x71, 0x72):
                callee_idx = struct.unpack('<H', insns[i+2:i+4])[0]
                cname = get_method(callee_idx)
                if any(k in cname.lower() for k in ['bluetooth', 'codec', 'audio', 'device']):
                    print(f"    invoke {cname}")
