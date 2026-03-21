with open('main.py', 'r') as f:
    content = f.read()

content = content.replace("    from shared.stego_lab import run_stego_lab_logic\nfrom shared.typegen_lab import run_typegen_lab_logic\n    run_stego_lab_logic(args)", "    from shared.stego_lab import run_stego_lab_logic\n    run_stego_lab_logic(args)")

with open('main.py', 'w') as f:
    f.write(content)
