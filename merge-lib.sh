#!/bin/sh

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
  