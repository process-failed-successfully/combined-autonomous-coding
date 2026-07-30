import re
with open("tests/test_base64img.py", "r") as f:
    data = f.read()

# .renderable is removed in Textual > 0.x, they likely just mean to check .render() or check str(status) which works on older Textual too but wait, actually just using .renderable on Textual 0.50+ is an error because they removed it. It should be .renderable on Textual < 0.60, wait, it's textual 0.86 ? No.
# I will just replace `.renderable` with `.render()` or cast to str(status.render())
data = data.replace(".renderable", ".render()")
with open("tests/test_base64img.py", "w") as f:
    f.write(data)
