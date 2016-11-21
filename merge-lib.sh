#!/bin/sh
#-------------------------------------------------------------------------------
#
#    Project: KiCad Tools
#    
#    Name:    Merge Libraries Script
#   
#    Purpose: Merge schematic components to libraries
#
#    Copyright (c) 2016, emb-lib Project Team
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining  a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
#    THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#-------------------------------------------------------------------------------

if [ -z $1 ]; then
    echo 'No library name specified'
    return
fi

echo 'EESchema-LIBRARY Version 2.3' > $1.lib
echo '#encoding utf-8' >> $1.lib
cat *.cmp >> $1.lib
echo '#' >> $1.lib
echo '#End Library' >> $1.lib

echo 'EESchema-DOCLIB  Version 2.0' > $1.dcm
cat *.dcmp >> $1.dcm
echo '#' >> $1.dcm
echo '#End Doc Library' >> $1.dcm

echo "Create $1.lib"
  