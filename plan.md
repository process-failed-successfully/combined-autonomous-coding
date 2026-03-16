# Plan: Add a `MsgpackLab` (MessagePack format utility)

1. **Feature**: A `msgpack-lab` utility to pack and unpack MessagePack data, similar to `cbor-lab`. MessagePack is an extremely popular binary serialization format.
2. **Commands**:
   - `encode`: Convert JSON to MessagePack.
   - `decode`: Convert MessagePack to JSON.
   - `tui`: A Textual-based UI for encoding/decoding.
3. **Files to create/modify**:
   - `shared/msgpack_lab.py`: Core logic for `MsgpackManager` and `run_msgpack_lab_logic`.
   - `shared/tui_msgpack.py`: The TUI component.
   - `shared/tui.py`: Import and register the new TUI tab.
   - `main.py`: Add the CLI arguments for `msgpack-lab` and `msgpack`.
   - `tests/test_msgpack_lab.py`: Comprehensive tests for the new lab.
   - `requirements.txt`: Ensure `msgpack` is added if needed. (Will check if it exists).
4. **Pre-Commit**: Complete required pre-commit checks to ensure code passes format and type checking.

Let's check if `msgpack` library is in `requirements.txt`.
