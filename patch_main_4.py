with open('main.py', 'r') as f:
    content = f.read()

# Make sure we add import properly
if "from shared.typegen_lab import run_typegen_lab_logic" not in content:
    content = content.replace("from shared.stego_lab import run_stego_lab_logic\n", "from shared.stego_lab import run_stego_lab_logic\nfrom shared.typegen_lab import run_typegen_lab_logic\n")

with open('main.py', 'w') as f:
    f.write(content)
