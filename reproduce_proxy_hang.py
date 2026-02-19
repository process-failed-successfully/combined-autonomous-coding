import unittest
import os
from tests.test_proxy_lab import TestProxyLab

if __name__ == "__main__":
    # Simulate a bad proxy environment
    os.environ["HTTP_PROXY"] = "http://1.2.3.4:5678" # Non-existent proxy
    os.environ["HTTPS_PROXY"] = "http://1.2.3.4:5678"

    # We need to make sure 127.0.0.1 is NOT in NO_PROXY for this test to effectively break 'requests' if it respects env
    # But wait, requests usually ignores proxy for localhost unless configured otherwise?
    # Actually requests respects NO_PROXY.
    if "NO_PROXY" in os.environ:
        del os.environ["NO_PROXY"]

    unittest.main()
