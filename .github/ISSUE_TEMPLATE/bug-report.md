---
name: Bug Report
about: Report a bug encountered while operating Kubernetes
labels: kind/bug

---
<!--
Please, be ready for followup questions, and please respond in a timely
manner.  If we can't reproduce a bug or think a feature already exists, we
might close your issue.  If we're wrong, PLEASE feel free to reopen it and
explain why.
-->

**Environment**:
- **Cloud provider or hardware configuration:**

- **OS (`printf "$(uname -srm)\n$(cat /etc/os-release)\n"`):**

- **Version of Ansible** (`ansible --version`):


**Kubespray version (commit) (`git rev-parse --short HEAD`):**


**Network plugin used**:


**Copy of your inventory file:**


**Command used to invoke ansible**:


**Output of ansible run**:
<!-- We recommend using snippets services like https://gist.github.com/ etc. -->

**Anything else do we need to know**:
<!-- By running scripts/collect-info.yaml you can get a lot of useful informations.
Script can be started by:
ansible-playbook -i <inventory_file_path> -u <ssh_user> -e ansible_ssh_user=<ssh_user> -b --become-user=root -e dir=`pwd` scripts/collect-info.yaml
(If you using CoreOS remember to add '-e ansible_python_interpreter=/opt/bin/python').
After running this command you can find logs in `pwd`/logs.tar.gz. You can even upload somewhere entire file and paste link here.-->
