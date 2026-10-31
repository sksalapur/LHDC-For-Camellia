from elftools.elf.elffile import ELFFile

with open('miui_libbluetooth_jni.so', 'rb') as f:
    e = ELFFile(f)
    symtab = e.get_section_by_name('.dynsym')
    matches = []
    for sym in symtab.iter_symbols():
        name = sym.name
        if any(k in name.lower() for k in ['lhdc', 'a2dp_sourcecodecindex', 'setpeercodeccapabilities', 'isselectionvalid']):
            matches.append((sym['st_value'], sym['st_size'], name))

for val, size, name in sorted(matches):
    print(f"0x{val:08x} (0x{size:04x}) {name}")
