# Terraform-AWS-VPN-Guide
- VPN Connection을 위한 기본 설정(*)  
  file: contrib/terraform/aws/terraform.tfvars
  ```
  vpn_connection_enable = false
  ```
  > `false` : VPN Connection 비활성화  
  > `true` : VPN Connection 활성화
  ```
  customer_gateway_ip = AWS TGW와 VPN 연결을 하기 위한 Customer측 Gateway Public IP
  ```
  > ex) customer_gateway_ip = "125.209.222.141"
  ```
  local_cidr = On-Premise의 Private CIDR
  ```
  > ex) local_cidr = "172.16.3.0/24"

- VPN Connection을 위한 세부 설정(optional)  
  file: contrib/terraform/aws/vpn/variable.tf  
  ```
  주의: BGP가 활성화 되어있지 않은 경우, 아래 variable들은 기본 설정 유지
  ```
  > vpn_connection_static_routes_only = `true`  
  > propagateion_enable = `false`
