# I am ansible.module_utils.external1 for any module that does not have an
# adjacent module_utils directory overriding the name, since I appear in the
# 'module_utils' path in ansible.cfg.

from ansible.module_utils import external2

def path():
    return "ansible/integration/module_utils/module_utils/external1.py"

def path2():
    return external2.path()
