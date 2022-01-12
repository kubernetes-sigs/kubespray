# Terraform-aws-provisioning-guide


## 구성요소 및 버전
* Terraform v1.1.2


## Prerequisites

1. AWS IAM에서 terraform이 사용할 IAM 계정을 발급받는다. 

   사용자 이름을 적절히 입력하고, AWS 액세스 유형은 ***액세스 키 - 프로그래밍 방식 액세스*** 를 선택한다. 

   권한에 AWS 자원생성에 맞는 권한들을 넣거나, 기존의 그룹에 연결하고 IAM사용자를 생성한다.

   생성시 표기되는 액세스키 ID와 Secret Key를 저장한다.

2. STS 엔트포인트 설정 (서울 외 타 리전 선택시)

   IAM - 액세스 관리 - 계정설정 에서 STS(보안 토큰 서비스) 단락의 글로벌 엔트포인트 좌측 편집을 클릭해 세션 토큰의 리전 호환성을 '모든 AWS 리전에서 유효' 를 선택하고 저장한다. 

3. Keypair 발급

   인스턴스를 생성하고자 하는 리전에서 EC2-네트워크 및 보안-키 페어를 선택해 접근한다.

   키페어 생성을 클릭하여 이름, 키페어 유형 프라이빗 키 파일 형식을 선택하고 키 페어 생성을 클릭한다. 생성 키 선택시 표기되는 .pem 파일을 반드시 저장한다. 


## Install terraform, kubespray

1. (aws 인스턴스가 없는 경우) terraform을 설치한다.
```yml
// repo 등록
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo

// terraform 설치
yum --showduplicate list terraform
sudo yum -y install terraform

// 설치 확인
terraform  version
```

2. kubespray를 설치한다.
```yml   
git clone https://github.com/tmax-cloud/kubespray.git 
```

## Terraform setting

1. terraform config
2. terraform apply

### Terraform config

1. terraform.tfvars 설정 (kubespray/contrib/terraform/aws/terraform.tfvars)

   ```
   #Global Vars
   aws_cluster_name = "supercloud" // 클러스터 네임
   
   #VPC Vars
   aws_vpc_cidr_block       = "10.0.0.0/18" // VPC대역대 설정
   // 폐쇠망 subnet CIDR
   aws_cidr_subnets_private = ["10.0.1.0/24", "10.0.3.0/24", "10.0.5.0/24"]
   // 외부망 subnet CIDR
   aws_cidr_subnets_public  = ["10.0.2.0/24", "10.0.4.0/24", "10.0.6.0/24"]
      
   #Bastion Host
   aws_bastion_num  = 2
   aws_bastion_size = "t3.small" // bastion 인스턴스 타입
   
   #Kubernetes Cluster
   
   aws_kube_master_num  = 3	// 마스터노드 갯수
   aws_kube_master_size = "m5.2xlarge"	// 마스터노드 인스턴스 타입
   
   aws_etcd_num  = 0			// etcd가 마스터 내부에 포함.	
   #aws_etcd_num  = 3				// etcd가 별도의 인스턴스에 생성됨. 이때 인스턴스 갯수
   aws_etcd_size = ""m5.2xlarge""		// etcd 인스턴스 타입
   
   aws_kube_worker_num  = 3		// worker노드 갯수
   aws_kube_worker_size = "m5.2xlarge"		// worker 노드 인스턴스 타입
   
   #Settings AWS ELB
   
   aws_elb_api_port                = 6443
   k8s_secure_api_port             = 6443
   #kube_insecure_apiserver_address = "0.0.0.0"
   
   default_tags = {
     #  Env = "devtest"
     #  Product = "kubernetes"
   }
   
   inventory_file = "../../../inventory/tmaxcloud/hosts"	// hosts 파일 경로
   ```
   
   - VPC는 한 리전당 생성 가능한 갯수 및 할당량이 존재하므로 적절히 고려하여 인스턴스를 생성한다.
   - Subnet 설정에서 리스트 안의 갯수를 늘리면 그에따라 여러 존에 Subnet을 생성하고 노드를 배포한다. Ex) ["10.0.1.0/24", "10.0.3.0/24"]로 설정하면 2개의 zone에 배포(AZ2). 
   - 인스턴스 유형의 정보는 https://aws.amazon.com/ko/ec2/instance-types 을 참조한다.
   
2. ami(이미지) 설정 (kubespray/contrib/terraform/aws/variable.tf)

   ```
   data "aws_ami" "distro" {
     most_recent = true
   
     filter {
       name   = "name"
       values = ["CentOS 8.4.2105 x86_64"]
     }
   
      owners =["125523088429"]
   } 
   ```

   사용하고자 하는 ami 정보를 해당 부분에 작성하여 저장한다. 
   - AMI 정보 검색 방법
     1. AWS Console에 로그인하여 EC2로 접근한다. 
     2. 탐색창에서 AMI를 선택한다. 
     3. 필터를 적절하게 설정해 검색을 하여 사용할 이미지를 검색한다.

### terraform apply

1. credentials.tfvars 생성 

   ```
   #AWS Access Key
   AWS_ACCESS_KEY_ID = "" // IAM 계정 생성시 발급받은 액세스 키 ID
   #AWS Secret Key
   AWS_SECRET_ACCESS_KEY = ""  // IAM 계정 생성시 발급받은 액세스 키의 secret Key
   #EC2 SSH Key Name
   AWS_SSH_KEY_NAME = ""  // 키페어 생성시 입력한 이름
   #AWS Region
   AWS_DEFAULT_REGION = "eu-central-1"  // 생성하고자 하는 region 명 
   ```

   - 키페어는 region에 귀속되므로 다른 region의 키페어를 입력하면 에러가 발생한다. 생성하고자 하는 region에 맞는 키페어를 입력해야한다. 
   - region 명은 'ap-northeast-2' 와 같이 코드명으로 입력.

2. aws instance 생성

```yml   
terraform apply -var-file=credentials.tfvars
```

## Troubleshooting

### SSH 관련이슈

1. AWS에서의 보안 그룹, 네트워크ACL을 확인

   AWS-VPC-보안 탭의 네트워크 ACL과 보안그룹의 Inbound/Outbound 규칙을 확인하여 필요로 하는 룰을 추가한다.

2. Ansible-playbook 명령시 ssh permission error
   
   - ec2생성에 넣었던 키페어 파일의 권한을 확인한다. (chmod 400 terraform.pem)
   - ansible 명령에서 keypire를 넣어주는 것이 아닌, .ssh에 .pem 파일을 넣고 ssh-add를 수행해 keypair가 시스템에 등록되도록 한다.
   
3. Ec2 root 계정으로 ssh접근방법 

   일반 계정으로 로그인 한다.

   - CentOs 기준으로 다음과 같이 접속한다.
   - `ssh -i PrivateKey.pem centos@Floating-IP-Address`

   접속 후 **sudo -s** 로 관리자 권한으로 변경한다.

   ```
   /root/.ssh/authorized_keys
   ```

   파일을 열어서(vim 등) 아래의 내용을 찾아서 수정한다.

   - `sh-rsa` 부분부터 시작하도록 앞의 내용을 지워준다.

   ```
   /etc/ssh/sshd_config
   ```

   파일을 열어서 아래의 항목을 수정한다.

   - `PermitRootLogin yes`

   3~4 작업 후 `systemctl restart sshd` 로 서비스를 재시작 해준다.

