#!/bin/sh

cat lib-head *.cmp lib-tail > lib.lib

if [ $1 ]; then
    mv lib.lib $1
fi