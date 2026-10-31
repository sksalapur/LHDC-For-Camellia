import struct

with open('payload.bin', 'rb') as f:
    magic = f.read(4)
    file_format_version = struct.unpack('>Q', f.read(8))[0]
    manifest_size = struct.unpack('>Q', f.read(8))[0]
    print(f"Manifest size: {manifest_size} bytes")
    manifest_bytes = f.read(manifest_size)
    
    # search for partition names (usually string literals in protobuf)
    import re
    # In DeltaArchiveManifest protobuf, PartitionUpdate has partition_name
    strings = re.findall(rb'[a-z_]{3,20}', manifest_bytes)
    common_parts = {'system', 'vendor', 'product', 'system_ext', 'boot', 'odm'}
    found_parts = set()
    for s in strings:
        s_dec = s.decode('utf-8', 'ignore')
        if s_dec in common_parts:
            found_parts.add(s_dec)
    print("Partitions found in payload.bin:", found_parts)
