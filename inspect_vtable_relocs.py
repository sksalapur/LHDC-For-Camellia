import struct
from parse_elf_symbols import parse_elf

symbols = {val: name for val, size, name in parse_elf('miui_libbluetooth_jni.so')}

with open('miui_libbluetooth_jni.so', 'rb') as f:
    data = f.read()

# Parse section headers to find .rela.dyn
e_shoff = struct.unpack('<Q', data[40:48])[0]
e_shentsize = struct.unpack('<H', data[58:60])[0]
e_shnum = struct.unpack('<H', data[60:62])[0]
e_shstrndx = struct.unpack('<H', data[62:64])[0]

sections = []
for i in range(e_shnum):
    off = e_shoff + i * e_shentsize
    sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = struct.unpack('<IIQQQQIIQQ', data[off:off+64])
    sections.append({
        'name_idx': sh_name, 'type': sh_type, 'flags': sh_flags, 'addr': sh_addr,
        'offset': sh_offset, 'size': sh_size, 'entsize': sh_entsize
    })

shstr = data[sections[e_shstrndx]['offset'] : sections[e_shstrndx]['offset'] + sections[e_shstrndx]['size']]
def get_str(sec_data, idx):
    end = sec_data.find(b'\x00', idx)
    return sec_data[idx:end].decode('utf-8', 'ignore') if end != -1 else ''

for s in sections:
    s['name'] = get_str(shstr, s['name_idx'])

rela_sec = next((s for s in sections if s['name'] == '.rela.dyn'), None)
relocs = {}
if rela_sec:
    count = rela_sec['size'] // 24
    for i in range(count):
        off = rela_sec['offset'] + i * 24
        r_offset, r_info, r_addend = struct.unpack('<QQq', data[off:off+24])
        r_type = r_info & 0xffffffff
        relocs[r_offset] = (r_type, r_addend)

vtable_addr = 0x00e77128 + 16 # vtable methods start at +16 after RTTI
print(f"Vtable for A2dpCodecConfigLhdcV3 (RTTI at 0x{vtable_addr-8:08x}):")
for i in range(15):
    entry = vtable_addr + i * 8
    if entry in relocs:
        rtype, raddend = relocs[entry]
        name = symbols.get(raddend, f"func_0x{raddend:x}")
        print(f"  vtable[{i:02d}] (entry 0x{entry:x}) -> 0x{raddend:08x} : {name}")
    else:
        print(f"  vtable[{i:02d}] (entry 0x{entry:x}) -> not in rela.dyn")
