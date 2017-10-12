Debian Jessie
===============

Debian Jessie Pre-Installation Notes:
- Add 
  
  ```GRUB_CMDLINE_LINUX="cgroup_enable=memory swapaccount=1"```
  
  to /etc/default/grub. Then update with
  
  ```
   sudo update-grub
   sudo update-grub2
   sudo reboot
  ```
  
- Add the [backports](https://backports.debian.org/Instructions/) which contain Systemd 2.30.
  
  The needed "Delegate" directive is not supported in service files by the default Systemd version (2.15)
  Then reinstall Systemd
  
  ```apt-get -t jessie-backports install systemd```
  
- Add the Ansible repository and install ansible

  ```
  sudo add-apt-repository ppa:ansible/ansible
  sudo apt-get update
  sudo apt.get install ansible

  ```

- Install Jinja2 and Python-Netaddr

  ```sudo apt-get install phyton-jinja2=2.8-1~bpo8+1 python-netaddr```
  
  
Now you can continue with [Preparing your deployment](getting-started.md#starting-custom-deployment)
