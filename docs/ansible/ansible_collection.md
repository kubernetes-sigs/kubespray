# Ansible collection

Kubespray can be installed as an [Ansible collection](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html).

## Usage

1. Set up an inventory with the appropriate host groups and required group vars.
   See also the documentation on [kubespray inventories](./inventory.md) and the
   general ["Getting started" documentation](../getting_started/getting-started.md#building-your-own-inventory).

2. Add Kubespray to your requirements.yml file

   ```yaml
   collections:
   - name: https://github.com/kubernetes-sigs/kubespray
     type: git
     version: master # use the appropriate tag or branch for the version you need
   ```

3. Install your collection

   ```ShellSession
   ansible-galaxy install -r requirements.yml
   ```

4. Create a playbook to install your Kubernetes cluster

   ```yaml
   - name: Install Kubernetes
     ansible.builtin.import_playbook: kubernetes_sigs.kubespray.cluster
   ```

5. Update INVENTORY and PLAYBOOK so that they point to your inventory file and the playbook you created above, and then install Kubespray

   ```ShellSession
   ansible-playbook -i INVENTORY --become --become-user=root PLAYBOOK
   ```
