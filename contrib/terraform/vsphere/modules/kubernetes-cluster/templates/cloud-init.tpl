#cloud-config

ssh_authorized_keys:
%{ for ssh_public_key in ssh_public_keys ~}
  - ${ssh_public_key}
%{ endfor ~}
