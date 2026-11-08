import os
import zipfile

def make_zip(source_dir, output_zip):
    with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                # Convert backslashes to forward slashes for Linux/Android
                arcname = rel_path.replace('\\', '/')
                z.write(full_path, arcname)
                print(f"Added: {arcname}")

if __name__ == '__main__':
    make_zip('module', 'LHDC-for-Camellia.zip')
    print("Done packaging LHDC-for-Camellia.zip")
