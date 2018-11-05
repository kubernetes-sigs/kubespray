#!/bin/bash
# I consume 65535 bytes every 10ms, for testing mitogen.core.write_all()

while :; do
    read -n 65535
    sleep 0.01
done
