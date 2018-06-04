#!/usr/bin/env python
DOCUMENTATION = '''
---
module: hashivault_pki_issue
version_added: "0.1"
short_description: Hashicorp Vault PKI issue module
description:
    - Module to issue PKI certs from Hashicorp Vault.
options:
    url:
        description:
            - url for vault
        default: to environment variable VAULT_ADDR
    ca_cert:
        description:
            - "path to a PEM-encoded CA cert file to use to verify the Vault server TLS certificate"
        default: to environment variable VAULT_CACERT
    ca_path:
        description:
            - "path to a directory of PEM-encoded CA cert files to verify the Vault server TLS certificate : if ca_cert is specified, its value will take precedence"
        default: to environment variable VAULT_CAPATH
    client_cert:
        description:
            - "path to a PEM-encoded client certificate for TLS authentication to the Vault server"
        default: to environment variable VAULT_CLIENT_CERT
    client_key:
        description:
            - "path to an unencrypted PEM-encoded private key matching the client certificate"
        default: to environment variable VAULT_CLIENT_KEY
    verify:
        description:
            - "if set, do not verify presented TLS certificate before communicating with Vault server : setting this variable is not recommended except during testing"
        default: to environment variable VAULT_SKIP_VERIFY
    authtype:
        description:
            - "authentication type to use: token, userpass, github, ldap, approle"
        default: token
    token:
        description:
            - token for vault
        default: to environment variable VAULT_TOKEN
    username:
        description:
            - username to login to vault.
        default: to environment variable VAULT_USER
    password:
        description:
            - password to login to vault.
        default: to environment variable VAULT_PASSWORD
    secret:
        description:
            - secret to read.
    data:
        description:
            - Keys and values to write.
    update:
        description:
            - Update rather than overwrite.
        default: False
    min_ttl:
        description:
            - Issue new cert if existing cert has lower TTL expressed in hours or a percentage. Examples: 70800h, 50%
    force:
        description:
            - Force issue of new cert

'''
EXAMPLES = '''
---
- hosts: localhost
  tasks:
    - hashivault_write:
        secret: giant
        data:
            foo: foe
            fie: fum
'''


def main():
    argspec = hashivault_argspec()
    argspec['secret'] = dict(required=True, type='str')
    argspec['update'] = dict(required=False, default=False, type='bool')
    argspec['data'] = dict(required=False, default={}, type='dict')
    module = hashivault_init(argspec, supports_check_mode=True)
    result = hashivault_write(module)
    if result.get('failed'):
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def _convert_to_seconds(original_value):
    try:
        value = str(original_value)
        seconds = 0
        if 'h' in value:
            ray = value.split('h')
            seconds = int(ray.pop(0)) * 3600
            value = ''.join(ray)
        if 'm' in value:
            ray = value.split('m')
            seconds += int(ray.pop(0)) * 60
            value = ''.join(ray)
        if value:
            ray = value.split('s')
            seconds += int(ray.pop(0))
        return seconds
    except Exception:
        pass
    return original_value

def hashivault_needs_refresh(old_data, min_ttl):
     print("Checking refresh")
     print_r(old_data)
     return False
#    if sorted(old_data.keys()) != sorted(new_data.keys()):
#        return True
#    for key in old_data:
#        old_value = old_data[key]
#        new_value = new_data[key]
#        if old_value == new_value:
#            continue
#        if key != 'ttl' and key != 'max_ttl':
#            return True
#        old_value = _convert_to_seconds(old_value)
#        new_value = _convert_to_seconds(new_value)
#        if old_value != new_value:
#            return True
#    return False
#
def hashivault_changed(old_data, new_data):
    if sorted(old_data.keys()) != sorted(new_data.keys()):
        return True
    for key in old_data:
        old_value = old_data[key]
        new_value = new_data[key]
        if old_value == new_value:
            continue
        if key != 'ttl' and key != 'max_ttl':
            return True
        old_value = _convert_to_seconds(old_value)
        new_value = _convert_to_seconds(new_value)
        if old_value != new_value:
            return True
    return False


from ansible.module_utils.hashivault import *


@hashiwrapper
def hashivault_write(module):
    result = {"changed": False, "rc": 0}
    params = module.params
    client = hashivault_auth_client(params)
    secret = params.get('secret')
    force = params.get('force', False)
    min_ttl = params.get('min_ttl', "100%")
    returned_data = None
    
    if secret.startswith('/'):
        secret = secret.lstrip('/')
    #else:
    #    secret = ('secret/%s' % secret)
    data = params.get('data')
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        changed = True
        write_data = data

        if params.get('update') or module.check_mode:
            # Do not move this read outside of the update
            read_data = client.read(secret) or {}
            read_data = read_data.get('data', {})

            write_data = dict(read_data)
            write_data.update(data)

            result['write_data'] = write_data
            result['read_data'] = read_data
            changed = hashivault_changed(read_data, write_data)
            if not changed:
                changed = hashivault_needs_refresh(read_data, min_ttl)
                
        if changed:
            if not module.check_mode:
                returned_data = client.write((secret), **write_data)

            if returned_data:
                result['data'] = returned_data
            result['msg'] = "Secret %s written" % secret
        result['changed'] = changed
    return result


if __name__ == '__main__':
    main()

