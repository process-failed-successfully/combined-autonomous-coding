# The `test_main.py` is generating a MagicMock file artifact because it mocks something incorrectly. Let's find it.
import os
import glob
print(glob.glob("<MagicMock*"))
