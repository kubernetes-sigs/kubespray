# Terraform's AWS ELB setting
- Create Kube API ELB type as public or private  
  file: contrib/terraform/aws/terraform.tfvars  
  ```
  aws_elb_api_internal = false
  ```
  `false` : Public  
  `true`  : Private  
