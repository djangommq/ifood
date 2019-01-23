#!/bin/bash
while [ 1 ]
do
    cd ~/ifood
    git checkout .
    git pull gitlab master
done
