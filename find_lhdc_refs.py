import zipfile, struct

with zipfile.ZipFile('timbre.apk', 'r') as z:
    for dex_name in ['classes.dex', 'classes2.dex']:
        data = z.read(dex_name)
        # Find string ID for 'LHDCv5'
        # DEX string_ids
        string_ids_size = struct.unpack('<I', data[56:60])[0]
        string_ids_off = struct.unpack('<I', data[60:64])[0]
        lhdc_str_idx = -1
        for i in range(string_ids_size):
            str_data_off = struct.unpack('<I', data[string_ids_off + i*4 : string_ids_off + (i+1)*4])[0]
            # uleb128 length followed by MUTF-8
            # skip uleb128
            idx = str_data_off
            while data[idx] & 0x80: idx += 1
            idx += 1
            end = data.find(b'\x00', idx)
            s = data[idx:end]
            if s == b'LHDCv5':
                lhdc_str_idx = i
                print(f"Found 'LHDCv5' as string_id {i} in {dex_name}")
                break
        
        if lhdc_str_idx != -1:
            # Search for const-string opcode: 0x1a <reg> <string_id_16> or 0x1b <reg> <string_id_32>
            p16 = struct.pack('<BH', 0x1a, lhdc_str_idx)
            pos = 0
            while True:
                p = data.find(p16, pos)
                if p == -1: break
                print(f"const-string in {dex_name} at offset 0x{p:x}")
                pos = p + 3
