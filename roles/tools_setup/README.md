# tools_setup

The purpose of this role is to setup tools used by subsequents steps of
Kubespray playbooks on both the Ansible control node and the the managed node.
It only deals with things download directly by kubespray (in
`roles/download/file`), not packages installed from distributions repositories.
