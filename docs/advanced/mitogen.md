# Mitogen

*Warning:* Mitogen support is now deprecated in kubespray due to upstream not releasing an updated version to support ansible 4.x (ansible-base 2.11.x) and above. The CI support has been stripped for mitogen and we are no longer validating any support or regressions for it. The supporting mitogen install playbook and integration documentation will be removed in a later version.

[Mitogen for Ansible](https://mitogen.networkgenomics.com/ansible_detailed.html) allow a 1.25x - 7x speedup and a CPU usage reduction of at least 2x, depending on network conditions, modules executed, and time already spent by targets on useful work. Mitogen cannot improve a module once it is executing, it can only ensure the module executes as quickly as possible.

## Install

```ShellSession
ansible-playbook contrib/mitogen/mitogen.yml
```

The above playbook sets the ansible `strategy` and `strategy_plugins` in `ansible.cfg` but you can also enable them if you use your own `ansible.cfg` by setting the environment varialbles:

```ShellSession
export ANSIBLE_STRATEGY=mitogen_linear
export ANSIBLE_STRATEGY_PLUGINS=plugins/mitogen/ansible_mitogen/plugins/strategy
```

... or `ansible.cfg` setup:

```ini
[defaults]
strategy_plugins = plugins/mitogen/ansible_mitogen/plugins/strategy
strategy=mitogen_linear
```

## Limitation

If you are experiencing problems, please see the [documentation](https://mitogen.networkgenomics.com/ansible_detailed.html#noteworthy-differences).
