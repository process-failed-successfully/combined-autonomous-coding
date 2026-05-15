from PIL import Image
try:
    from shared.favicon_lab import FaviconManager
    HAS_FAVICON_DEPS = True
except ImportError as e:
    print(f"Error importing FaviconManager: {e}")
    HAS_FAVICON_DEPS = False
print(f"HAS_FAVICON_DEPS: {HAS_FAVICON_DEPS}")
