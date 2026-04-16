with open('shared/mongo_lab.py', 'r') as f:
    lines = f.readlines()

out = []
for line in lines:
    if line.strip() == '':
        if out and out[-1].strip() == '':
            if len(out) >= 2 and out[-2].strip() == '':
                continue
    out.append(line)
with open('shared/mongo_lab.py', 'w') as f:
    f.writelines(out)
