import re

with open(r'C:\Users\SKSAL\.gemini\antigravity-ide\brain\9c2410f4-8d1f-44f9-a816-03ae161dee5a\.system_generated\steps\540\content.md', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

for m in re.finditer(r'/Tools-cx-app/meta-magic_mount-rs/releases/download/[^"]+', text):
    print(m.group())
