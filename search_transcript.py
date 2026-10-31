import json

log_file = r'C:\Users\SKSAL\.gemini\antigravity-ide\brain\9c2410f4-8d1f-44f9-a816-03ae161dee5a\.system_generated\logs\transcript.jsonl'

with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'EvolutionX' in line or 'Lunaris' in line:
            obj = json.loads(line)
            content = obj.get('content', '')
            if isinstance(content, str) and ('EvolutionX' in content or 'Lunaris' in content):
                # print a short excerpt
                for sub in content.split('\n'):
                    if 'EvolutionX' in sub or 'Lunaris' in sub or 'rom' in sub.lower():
                        print(f"[{obj.get('step_index')}] {sub[:120]}")
