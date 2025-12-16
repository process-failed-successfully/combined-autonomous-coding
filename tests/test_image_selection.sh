#!/bin/bash
set -e

# Test 1: Invalid Key
echo "Running Test 1: Invalid Key"
if ./bin/start_agent --image invalid_key; then
    echo "❌ Test 1 Failed: Should have failed for invalid image key"
    exit 1
else
    echo "✅ Test 1 Passed: Failed as expected"
fi

# Test 2: Valid Key (Dry run using --help to avoid full startup)
echo "Running Test 2: Valid Key (python)"
OUTPUT=$(./bin/start_agent --image python --help 2>&1)
if echo "$OUTPUT" | grep -q "Using Dockerfile: .*images/python/Dockerfile"; then
    echo "✅ Test 2 Passed: Correct Dockerfile selected"
else
    echo "❌ Test 2 Failed: Output was:"
    echo "$OUTPUT"
    exit 1
fi

# Test 3: Valid Key (node)
echo "Running Test 3: Valid Key (node)"
OUTPUT=$(./bin/start_agent --image node --help 2>&1)
if echo "$OUTPUT" | grep -q "Using Dockerfile: .*images/node/Dockerfile"; then
    echo "✅ Test 3 Passed: Correct Dockerfile selected"
else
    echo "❌ Test 3 Failed: Output was:"
    echo "$OUTPUT"
    exit 1
fi

# Test 4: Default (no flag)
echo "Running Test 4: Default Key"
OUTPUT=$(./bin/start_agent --help 2>&1)
# Note: Manifest lookup for 'default' key returns images/python/Dockerfile
if echo "$OUTPUT" | grep -q "Using Dockerfile: .*images/python/Dockerfile"; then
    echo "✅ Test 4 Passed: Default Dockerfile selected"
else
    echo "❌ Test 4 Failed: Output was:"
    echo "$OUTPUT"
    exit 1
fi

echo "🎉 All tests passed!"

# Test 5: Custom Dockerfile
echo "Running Test 5: Custom Dockerfile Path"
OUTPUT=$(./bin/start_agent --image tests/CustomDockerfile --help 2>&1)
if echo "$OUTPUT" | grep -q "Using Dockerfile: .*tests/CustomDockerfile"; then
    echo "✅ Test 5 Passed: Custom Dockerfile selected"
else
    echo "❌ Test 5 Failed: Output was:"
    echo "$OUTPUT"
    exit 1
fi

