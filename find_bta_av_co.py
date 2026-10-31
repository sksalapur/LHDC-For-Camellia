from parse_elf_symbols import parse_elf

symbols = sorted(parse_elf('miui_libbluetooth_jni.so'), key=lambda x: x[0])
for val, size, name in symbols:
    if any(k in name.lower() for k in ['bta_av_co_audio', 'peer_supports', 'find_peer_by', 'a2dp_sourcecodecindex']):
        print(f"0x{val:08x} ({size}) {name}")
