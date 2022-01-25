# Terraform's AWS ELB setting
- Create Kube API ELB type as public or private  
  file: contrib/terraform/aws/terraform.tfvars  
  ```
  aws_elb_api_internal = false
  ```
  `false` : Public  
  `true`  : Private  

- Whether to create Kube API ELB attach to Private or Public subnets
  file: contrib/terraform/aws/terraform.tfvars  
  ```
  aws_elb_api_public_subnet = true
  ```
  `false` : Attach Kube API ELB to Private subnets
  `true`  : Attach Kube API ELB to Public subnets
