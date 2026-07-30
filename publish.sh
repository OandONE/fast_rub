#!/bin/bash
# publish.sh - upload each package to PyPI and archive on success

VERSIONS_DIR="versions"

# Create versions directory if not exists
mkdir -p "$VERSIONS_DIR"

for file in dist/*; do
    echo "Uploading: $file"
    
    twine upload "$file"
    
    if [ $? -eq 0 ]; then
        echo "✓ Success. Moving $(basename "$file") to $VERSIONS_DIR/"
        mv "$file" "$VERSIONS_DIR/"
    else
        echo "✗ Failed. $(basename "$file") kept in dist/"
    fi
done