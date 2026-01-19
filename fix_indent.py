import sys

with open('shared/dependencies.py', 'r') as f:
    lines = f.readlines()

# Locate the lines
for i, line in enumerate(lines):
    if 'self.license_cache[package_name] = license_field' in line:
        # Check indent
        prefix = line[:line.find('self')]
        if len(prefix) != 20 or not prefix.strip() == '':
             print(f"Fixing line {i+1}: length {len(prefix)}")
             lines[i] = ' ' * 20 + 'self.license_cache[package_name] = license_field\n'
    if 'return license_field' in line and i > 0 and 'self.license_cache' in lines[i-1]:
         prefix = line[:line.find('return')]
         if len(prefix) != 20 or not prefix.strip() == '':
             print(f"Fixing line {i+1}: length {len(prefix)}")
             lines[i] = ' ' * 20 + 'return license_field\n'

with open('shared/dependencies.py', 'w') as f:
    f.writelines(lines)
