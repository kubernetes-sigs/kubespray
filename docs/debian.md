# Debian Jessie

Debian Jessie installation Notes:

- Add
  
  ```GRUB_CMDLINE_LINUX="cgroup_enable=memory swapaccount=1"```
  
  to /etc/default/grub. Then update with
  
  ```ShellSession
   sudo update-grub
   sudo update-grub2
   sudo reboot
  ```
  
- Add the [backports](https://backports.debian.org/Instructions/) which contain Systemd 2.30 and update Systemd.
  
  ```apt-get -t jessie-backports install systemd```
  
  (Necessary because the default Systemd version (2.15) does not support the "Delegate" directive in service files)
  
- Add the Ansible repository and install Ansible to get a proper version

  ```ShellSession
  sudo add-apt-repository ppa:ansible/ansible
  sudo apt-get update
  sudo apt-get install ansible

  ```

- Install Jinja2 and Python-Netaddr

  ```sudo apt-get install python-jinja2=2.8-1~bpo8+1 python-netaddr```
  
Now you can continue with [Preparing your deployment](getting-started.md#starting-custom-deployment)
