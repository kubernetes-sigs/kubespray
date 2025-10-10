#!/usr/bin/env python

import json
import os
import sys

with open(os.getenv("BASE_INVENTORY_FILE"), "r") as inventory_file:
    inventory = json.load(inventory_file)
index = int(os.getenv("INDEX"))
rotation = int(os.getenv("ROTATION", "0"))
kube_cp = (
    inventory["new_kube_control_plane"]["hosts"][:index]
    + inventory["kube_control_plane"]["hosts"][
        slice(None, None if index == 0 else -index)
    ]
)
kube_cp = kube_cp[rotation:] + kube_cp[:rotation]
inventory["kube_control_plane"]["hosts"] = kube_cp
etcd_cp = (
    inventory["new_etcd"]["hosts"][:index]
    + inventory["etcd"]["hosts"][slice(None, None if index == 0 else -index)]
)
etcd_cp = etcd_cp[rotation:] + etcd_cp[:rotation]
inventory["etcd"]["hosts"] = etcd_cp
json.dump(inventory, fp=sys.stdout)
