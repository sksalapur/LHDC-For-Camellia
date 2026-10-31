with open('classes_orig.dex', 'rb') as f:
    d = f.read()

import struct
string_ids_size, string_ids_off = struct.unpack_from('<II', d, 0x38)
type_ids_size, type_ids_off = struct.unpack_from('<II', d, 0x40)
proto_ids_size, proto_ids_off = struct.unpack_from('<II', d, 0x48)
field_ids_size, field_ids_off = struct.unpack_from('<II', d, 0x50)
method_ids_size, method_ids_off = struct.unpack_from('<II', d, 0x58)

def get_string(idx):
    if idx >= string_ids_size: return f'<str {idx}>'
    str_data_off, = struct.unpack_from('<I', d, string_ids_off + idx * 4)
    pos = str_data_off
    while d[pos] & 0x80: pos += 1
    pos += 1
    end = d.find(b'\x00', pos)
    return d[pos:end].decode('utf-8', errors='replace')

def get_type(idx):
    if idx >= type_ids_size: return f'<type {idx}>'
    descriptor_idx, = struct.unpack_from('<I', d, type_ids_off + idx * 4)
    return get_string(descriptor_idx)

def get_method(idx):
    if idx >= method_ids_size: return f'<method {idx}>'
    class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', d, method_ids_off + idx * 8)
    return f'{get_type(class_idx)}->{get_string(name_idx)}'

def get_field(idx):
    if idx >= field_ids_size: return f'<field {idx}>'
    class_idx, type_idx, name_idx = struct.unpack_from('<HHI', d, field_ids_off + idx * 8)
    return f'{get_type(class_idx)}->{get_string(name_idx)}:{get_type(type_idx)}'

pc = 0x2282e0
end_pc = 0x228460
while pc < end_pc:
    op = d[pc]
    line = f'{hex(pc)}: {op:02x}'
    if op == 0x00:
        line += f' nop'
        pc += 2
    elif op == 0x01:
        line += f' move v{d[pc+1]&0xf}, v{d[pc+1]>>4}'
        pc += 2
    elif op == 0x07:
        line += f' move-object v{d[pc+1]&0xf}, v{d[pc+1]>>4}'
        pc += 2
    elif op == 0x0a:
        line += f' move-result v{d[pc+1]}'
        pc += 2
    elif op == 0x0c:
        line += f' move-result-object v{d[pc+1]}'
        pc += 2
    elif op == 0x0e:
        line += f' return-void'
        pc += 2
    elif op == 0x0f:
        line += f' return v{d[pc+1]}'
        pc += 2
    elif op == 0x12:
        line += f' const/4 v{d[pc+1]&0xf}, #{d[pc+1]>>4}'
        pc += 2
    elif op == 0x13:
        val, = struct.unpack_from('<h', d, pc+2)
        line += f' const/16 v{d[pc+1]}, #{val}'
        pc += 4
    elif op == 0x1a:
        s_idx, = struct.unpack_from('<H', d, pc+2)
        line += f' const-string v{d[pc+1]}, "{get_string(s_idx)}"'
        pc += 4
    elif op == 0x22:
        t_idx, = struct.unpack_from('<H', d, pc+2)
        line += f' new-instance v{d[pc+1]}, {get_type(t_idx)}'
        pc += 4
    elif op == 0x28:
        off = struct.unpack_from('<b', d, pc+1)[0]
        line += f' goto {hex(pc + off*2)}'
        pc += 2
    elif op == 0x32:
        off, = struct.unpack_from('<h', d, pc+2)
        line += f' if-eq v{d[pc+1]&0xf}, v{d[pc+1]>>4}, {hex(pc + off*2)}'
        pc += 4
    elif op == 0x33:
        off, = struct.unpack_from('<h', d, pc+2)
        line += f' if-ne v{d[pc+1]&0xf}, v{d[pc+1]>>4}, {hex(pc + off*2)}'
        pc += 4
    elif op == 0x38:
        off, = struct.unpack_from('<h', d, pc+2)
        line += f' if-eqz v{d[pc+1]}, {hex(pc + off*2)}'
        pc += 4
    elif op == 0x39:
        off, = struct.unpack_from('<h', d, pc+2)
        line += f' if-nez v{d[pc+1]}, {hex(pc + off*2)}'
        pc += 4
    elif op == 0x54:
        f_idx, = struct.unpack_from('<H', d, pc+2)
        line += f' iget-object v{d[pc+1]&0xf}, v{d[pc+1]>>4}, {get_field(f_idx)}'
        pc += 4
    elif op == 0x59:
        f_idx, = struct.unpack_from('<H', d, pc+2)
        line += f' iput v{d[pc+1]&0xf}, v{d[pc+1]>>4}, {get_field(f_idx)}'
        pc += 4
    elif op == 0x6e:
        m_idx, = struct.unpack_from('<H', d, pc+2)
        line += f' invoke-virtual {get_method(m_idx)}'
        pc += 6
    elif op == 0x70:
        m_idx, = struct.unpack_from('<H', d, pc+2)
        line += f' invoke-direct {get_method(m_idx)}'
        pc += 6
    elif op == 0x71:
        m_idx, = struct.unpack_from('<H', d, pc+2)
        line += f' invoke-static {get_method(m_idx)}'
        pc += 6
    else:
        line += f' [raw {d[pc:pc+4].hex()}]'
        pc += 2
    print(line)
