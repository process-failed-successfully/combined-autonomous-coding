from PIL import Image

img = Image.new('RGB', (10, 10))

data = []
for y in range(img.height):
    for x in range(img.width):
        data.append(img.getpixel((x, y)))

print(len(data))
print(len(list(img.getdata())))
