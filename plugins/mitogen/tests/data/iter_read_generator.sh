#!/bin/bash
# I produce text every 100ms, for testing mitogen.core.iter_read()

i=0

while :; do
    i=$(($i + 1))
    echo "$i"
    sleep 0.1
done
