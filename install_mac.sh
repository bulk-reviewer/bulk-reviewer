#!/bin/bash

# Install dependencies
echo "Installing bulk_extractor dependencies and sleuthkit..."
brew install libewf afflib sleuthkit

# Install bulk_extractor 1.6.0-dev from fork
echo "Building bulk_extractor from source..."
git clone --recursive https://github.com/tw4l/bulk_extractor

# Export env vars so bulk_extractor does not complain that openssl isn't installed
export LDFLAGS="-L/usr/local/opt/openssl/lib -L/usr/local/lib -L/usr/local/opt/expat/lib"
export CFLAGS="-I/usr/local/opt/openssl/include/ -I/usr/local/include -I/usr/local/opt/expat/include"
export CPPFLAGS="-I/usr/local/opt/openssl/include/ -I/usr/local/include -I/usr/local/opt/expat/include"

# Build from source
cd bulk_extractor && \
    chmod 755 bootstrap.sh && \
    ./bootstrap.sh && \
    ./configure && \
    make && \
    make install

# Clean up bulk_extractor directory
echo "Cleaning up..."
if [ -d ../bulk_extractor ]
then
    rm -rf ../bulk_extractor
fi

echo "Complete."
