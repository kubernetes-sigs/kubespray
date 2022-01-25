instance-id: ${hostname}
local-hostname: ${hostname}
network:
  version: 2
  ethernets:
    ${interface_name}:
      match:
        name: ${interface_name}
      dhcp4: false
      addresses:
        - ${ip}/${netmask}
      gateway4: ${gw}
      nameservers:
        addresses: [${dns}]
