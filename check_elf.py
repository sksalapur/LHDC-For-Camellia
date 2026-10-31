import struct

def check_elf_dependencies(path):
    print('Checking dependencies of', path)
    with open(path, 'rb') as f:
        data = f.read()

    # ELF64 header
    e_ident = data[:16]
    if e_ident[:4] != b'\x7fELF':
        print('Not an ELF file')
        return

    e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags, e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx = struct.unpack('<HHIQQQIHHHHHH', data[16:64])
    
    # Read section headers
    shstrtab_off = e_shoff + e_shstrndx * e_shentsize
    sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size = struct.unpack('<IIQQQQ', data[shstrtab_off:shstrtab_off+40])[:6]
    shstrtab = data[sh_offset:sh_offset+sh_size]

    dynstr = b''
    needed = []
    soname = ''

    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link = struct.unpack('<IIQQQQI', data[off:off+44])[:7]
        name = shstrtab[sh_name:].split(b'\x00')[0].decode('latin1')
        if name == '.dynstr':
            dynstr = data[sh_offset:sh_offset+sh_size]

    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link = struct.unpack('<IIQQQQI', data[off:off+44])[:7]
        name = shstrtab[sh_name:].split(b'\x00')[0].decode('latin1')
        if name == '.dynamic':
            dyn_data = data[sh_offset:sh_offset+sh_size]
            for j in range(0, len(dyn_data), 16):
                d_tag, d_val = struct.unpack('<Qq', dyn_data[j:j+16])
                if d_tag == 1: # DT_NEEDED
                    dep = dynstr[d_val:].split(b'\x00')[0].decode('latin1')
                    needed.append(dep)
                elif d_tag == 14: # DT_SONAME
                    soname = dynstr[d_val:].split(b'\x00')[0].decode('latin1')
    
    print('SONAME:', soname)
    print('NEEDED:', needed)

check_elf_dependencies('spr_liblhdc/AOSP/other_so_files/enc/LHDC-magisk-11_arm64/system/lib64/liblhdcv5BT_enc.so')
check_elf_dependencies('spr_liblhdc/AOSP/other_so_files/enc/LHDC-magisk-11_arm64/system/lib64/liblhdcBT_enc.so')
check_elf_dependencies('spr_liblhdc/AOSP/other_so_files/enc/LHDC-magisk-11_arm64/system/lib64/liblhdcv5.so')
check_elf_dependencies('spr_liblhdc/AOSP/other_so_files/enc/LHDC-magisk-11_arm64/system/lib64/liblhdc.so')
