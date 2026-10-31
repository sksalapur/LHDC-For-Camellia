import struct

with open('miui_libbluetooth_jni.so', 'rb') as f:
    code = f.read()

from parse_elf_symbols import parse_elf
symbols = {val: name for val, size, name in parse_elf('miui_libbluetooth_jni.so')}

vtable_addr = 0x00e77128
print(f"Vtable for A2dpCodecConfigLhdcV3 at 0x{vtable_addr:08x}:")
for i in range(25):
    entry_addr = vtable_addr + i * 8
    fn_ptr = struct.unpack('<Q', code[entry_addr:entry_addr+8])[0]
    sym_name = symbols.get(fn_ptr, f"unknown_0x{fn_ptr:x}")
    print(f"  [{i:02d}] +0x{i*8:02x}: 0x{fn_ptr:08x} -> {sym_name}")
