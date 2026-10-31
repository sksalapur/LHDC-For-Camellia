import struct

with open('btsnoop_boot.cfa', 'rb') as f:
    hdr = f.read(16)
    records = []
    while True:
        rh = f.read(24)
        if len(rh) < 24:
            break
        orig_len, inc_len, flags, drops, ts = struct.unpack('>IIIIQ', rh)
        pkt = f.read(inc_len)
        records.append((flags, ts, pkt))

print(f'Total packets: {len(records)}')

for idx, (flags, ts, pkt) in enumerate(records):
    # HCI ACL packet: 0x02
    if pkt.startswith(b'\x02') and len(pkt) > 9:
        cid = struct.unpack('<H', pkt[7:9])[0]
        payload = pkt[9:]
        if len(payload) >= 2:
            sig = payload[1] & 0x3f
            msg_type = (payload[0] >> 2) & 0x03
            if sig in (1, 2, 3, 4, 5, 6, 7, 8, 9, 12):
                direction = 'RECV' if (flags & 1) else 'SENT'
                print(f'Pkt {idx} ({direction}) CID=0x{cid:04x} sig={sig} msg_type={msg_type}:')
                print('  Hex:', payload.hex(' '))




