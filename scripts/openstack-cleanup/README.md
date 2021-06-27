# openstack-cleanup

Tool to deletes openstack servers older than a specific age (default 4h).

Useful to cleanup orphan servers that are left behind when CI is manually cancelled or fails unexpectedly.

## Installation

```shell
pip install -r requirements.txt
python main.py --help
```

## Usage

```console
$ python main.py
This will delete VMs... (ctrl+c to cancel)
Will delete server example1
Will delete server example2
```
