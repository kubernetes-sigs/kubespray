#!/bin/bash
mkdir -p ssh
if ! [ -f ssh/id_rsa ] ; then
  ssh-keygen -N '' -t rsa -f ssh/id_rsa && cp ssh/id_rsa.pub ssh/authorized_keys
fi
