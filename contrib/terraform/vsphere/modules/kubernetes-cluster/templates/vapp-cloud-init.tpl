#cloud-config

ssh_authorized_keys:
%{ for ssh_public_key in ssh_public_keys ~}
  - ${ssh_public_key}
%{ endfor ~}

write_files:
  - path: /etc/netplan/10-user-network.yaml
    content: |.
      network:
        version: 2
        ethernets:
          ${interface_name}:
            dhcp4: false #true to use dhcp
            addresses:
            - ${ip}/${netmask}
            gateway4: ${gw} # Set gw here
            nameservers:
              addresses:
              - ${dns} # Set DNS ip address here

runcmd:
  - netplan apply
