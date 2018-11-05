#!/usr/bin/python

import json
from ansible.module_utils.basic import path

def main():
    print(json.dumps({
        'path': path()
    }))

if __name__ == '__main__':
    main()
