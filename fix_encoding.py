import sys

files = [
    'agent1_loader.py',
    'agent2_extractor.py', 
    'agent3_generator.py',
    'agent4_validator.py'
]

fix_line = "import sys\nsys.stdout.reconfigure(encoding='utf-8')\n\n"

for filename in files:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Only add if not already present
    if "sys.stdout.reconfigure" not in content:
        content = fix_line + content
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed: {filename}')
    else:
        print(f'Already fixed: {filename}')