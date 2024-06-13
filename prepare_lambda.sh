#!/bin/bash
rm function.zip
cd ..
mkdir tmp
cd hostregister
cp -R * ../tmp
cd ../tmp
pip3 install -r requirements.txt --target . --upgrade
zip -r9 ${OLDPWD}/function.zip .
cd ../hostregister
rm -rf ../tmp
