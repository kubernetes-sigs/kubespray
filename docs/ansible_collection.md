# Ansible collection

Kubespray can be installed as an [Ansible collection](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html).

## Requirements

- An inventory file with the appropriate host groups. See the [README](../README.md#usage).
- A `group_vars` directory. These group variables **need** to match the appropriate variable names under `inventory/local/group_vars`. See the [README](../README.md#usage).

## Usage

1. Add Kubespray to your requirements.yml file

   ```yaml
   collections:
   - name: https://github.com/kubernetes-sigs/kubespray
     type: git
     version: v2.23.0
   ```

2. Install your collection

   ```ShellSession
   ansible-galaxy install -r requirements.yml
   ```

3. Create a playbook to install your Kubernetes cluster

   ```yaml
   - name: Install Kubernetes
     ansible.builtin.import_playbook: kubernetes_sigs.kubespray.cluster
   ```

4. Update INVENTORY and PLAYBOOK so that they point to your inventory file and the playbook you created above, and then install Kubespray

   ```ShellSession
   ansible-playbook -i INVENTORY --become --become-user=root PLAYBOOK
   ```
