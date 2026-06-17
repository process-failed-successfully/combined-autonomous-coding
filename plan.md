1. **Analyze `image-lab` component:** I've explored `image-lab`, which provides basic capabilities (info, convert, resize, placeholder, exif manipulation, steganography).
2. **Identify missing feature:** Adding `crop`, `rotate`, and `flip` (or a combined `filter`/`transform` command) to `image-lab` is high-value and missing. A `crop` action is particularly useful for an image processing CLI.
3. **Proposed Plan:**
   - Add `crop`, `rotate`, and `flip` subcommands under `image-lab` in `main.py`.
   - Implement `crop(input, output, left, top, right, bottom)`, `rotate(input, output, degrees, expand)`, and `flip(input, output, direction)` in `shared/image_lab.py`'s `ImageLabManager` class.
   - Add argument parsing to `run_image_lab_logic` in `shared/image_lab.py`.
   - Write comprehensive unit tests in `tests/test_image_lab.py` using `unittest.mock.patch` to verify PIL is called correctly without requiring actual files (or with temp files if necessary).
   - Complete pre-commit steps to ensure testing, verification, review, and reflection.
