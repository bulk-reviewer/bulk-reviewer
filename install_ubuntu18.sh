#!/bin/bash

# Install bulk_extractor dependencies
echo "Installing bulk_extractor dependencies and sleuthkit..."
apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    flex \
    make \
    autoconf \
    libewf-dev \
    libssl-dev \
    libsqlite3-dev \
    scons \
    bison \
    libboost-dev \
    libicu-dev \
    libtool \
    sleuthkit \
&& rm -rf /var/lib/apt/lists/*

# Install bulk_extractor 1.6.0-dev from fork
echo "Building bulk_extractor from source..."
git clone --recursive https://github.com/tw4l/bulk_extractor

# Build from source
cd bulk_extractor && \
    chmod 755 bootstrap.sh && \
    ./bootstrap.sh && \
    ./configure --prefix=/usr/local && \
    make && \
    make install

# Clean up bulk_extractor directory
echo "Cleaning up..."
if [ -d ../bulk_extractor ]
then
    rm -rf ../bulk_extractor
fi

echo "Complete."
