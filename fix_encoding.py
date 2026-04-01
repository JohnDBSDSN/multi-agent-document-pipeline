import os

files = [
    'agent1_loader.py',
    'agent2_extractor.py',
    'agent3_generator.py',
    'agent4_validator.py'
]

for filename in files:
    # Read raw bytes
    with open(filename, 'rb') as f:
        raw = f.read()
    
    # Remove ALL BOM occurrences anywhere in file
    raw = raw.replace(b'\xef\xbb\xbf', b'')
    
    # Write back as clean bytes
    with open(filename, 'wb') as f:
        f.write(raw)
    
    print('Fixed: ' + filename)