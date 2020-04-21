# Mitogen

[Mitogen for Ansible](https://mitogen.networkgenomics.com/ansible_detailed.html) allow a 1.25x - 7x speedup and a CPU usage reduction of at least 2x, depending on network conditions, modules executed, and time already spent by targets on useful work. Mitogen cannot improve a module once it is executing, it can only ensure the module executes as quickly as possible.

## Install

```ShellSession
ansible-playbook mitogen.yml
```

## Limitation

If you are experiencing problems, please see the [documentation](https://mitogen.networkgenomics.com/ansible_detailed.html#noteworthy-differences).
