import struct

def parse_elf(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # ELF64 header
    assert data[:4] == b'\x7fELF'
    e_shoff = struct.unpack('<Q', data[40:48])[0]
    e_shentsize = struct.unpack('<H', data[58:60])[0]
    e_shnum = struct.unpack('<H', data[60:62])[0]
    e_shstrndx = struct.unpack('<H', data[62:64])[0]
    
    # Read section headers
    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = struct.unpack('<IIQQQQIIQQ', data[off:off+64])
        sections.append({
            'name_idx': sh_name, 'type': sh_type, 'flags': sh_flags, 'addr': sh_addr,
            'offset': sh_offset, 'size': sh_size, 'link': sh_link, 'info': sh_info,
            'entsize': sh_entsize
        })
    
    shstr = data[sections[e_shstrndx]['offset'] : sections[e_shstrndx]['offset'] + sections[e_shstrndx]['size']]
    def get_str(sec_data, idx):
        end = sec_data.find(b'\x00', idx)
        return sec_data[idx:end].decode('utf-8', 'ignore') if end != -1 else ''

    for s in sections:
        s['name'] = get_str(shstr, s['name_idx'])
    
    # Find .dynsym and .dynstr
    dynsym_sec = next((s for s in sections if s['name'] == '.dynsym'), None)
    dynstr_sec = next((s for s in sections if s['name'] == '.dynstr'), None)
    
    symbols = []
    if dynsym_sec and dynstr_sec:
        dynstr = data[dynstr_sec['offset'] : dynstr_sec['offset'] + dynstr_sec['size']]
        entsize = dynsym_sec['entsize'] or 24
        count = dynsym_sec['size'] // entsize
        for i in range(count):
            off = dynsym_sec['offset'] + i * entsize
            st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack('<IBBHQQ', data[off:off+24])
            sym_name = get_str(dynstr, st_name)
            symbols.append((st_value, st_size, sym_name))
            
    return symbols

symbols = parse_elf('miui_libbluetooth_jni.so')
matches = [(val, size, name) for val, size, name in symbols if any(k in name.lower() for k in ['lhdc', 'sourcecodecindex', 'setpeercodec', 'isselectionvalid', 'getallcapabilities', 'a2dpcodecconfig'])]
for val, size, name in sorted(matches):
    print(f"0x{val:08x} (0x{size:04x}) {name}")
