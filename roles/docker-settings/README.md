example:
```
ansible-playbook docker_settings.yml --extra-vars='docker_default_runtime=runc docker_config_insecure_registries=["1.1.1.1:5000"]' -vv
```