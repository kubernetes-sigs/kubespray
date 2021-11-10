# Terraform-aws-provisioning-guide

gilwoong_kang@tmax.co.kr

## 구성요소 및 버전

- Terraform v0.12.12

  \+ provider.aws v3.37.0

  \+ provider.null v3.1.0

  \+ provider.template v2.2.0

## Prerequisites

0. kubespray가 설치된 상태여야 합니다. 

1. AWS IAM에서 terraform이 사용할 IAM 계정을 발급받습니다. 

   사용자 이름을 적절히 입력하고, AWS 액세스 유형은 ***액세스 키 - 프로그래밍 방식 액세스*** 를 선택합니다. 

   권한에 AWS 자원생성에 맞는 권한들을 넣거나, 기존의 그룹에 연결하고 IAM사용자를 생성합니다.

   생성시 표기되는 액세스키 ID와 Secret Key를 저장해놓습니다.

2. STS 엔트포인트 설정 (서울 외 타 리전 선택시)

   IAM - 액세스 관리 - 계정설정 에서 STS(보안 토큰 서비스)단락의 글로벌 엔트포인트 좌측 편집을 클릭해 세션 토큰의 리전 호환성을 '모든 AWS 리전에서 유효' 를 선택하고 저장합니다. 

3. Keypair 발급

   인스턴스를 생성하고자 하는 리전에서 EC2-네트워크 및 보안-키 페어를 선택해 접근합니다.

   키페어 생성을 클릭하여 이름, 키페어 유형 프라이빗 키 파일 형식을 선택하고 키 페어 생성을 클릭합니다. 생성 키 선택시 표기되는 .pem 파일을 반드시 저장합니다. 

## terraform-setting

Terraform 

1. terraform config
2. terraform apply



kubespray 내부 terraform 패키지의 기본 경로는 다음과 같습니다.

`/kubespray-terraform/kubespray/contrib/terraform/aws`



### Terraform config

1. terraform.tfvars 설정

   ```
   #Global Vars
   aws_cluster_name = "devtest" // 클러스터 네임
   
   #VPC Vars
   aws_vpc_cidr_block       = "10.250.192.0/18" // VPC대역대 설정 /16~/18 /18 권장
   // 폐쇠망 subnet CIDR
   aws_cidr_subnets_private = ["10.250.192.0/20", "10.250.208.0/20"]
   // 외부망 subnet CIDR
   aws_cidr_subnets_public  = ["10.250.224.0/20", "10.250.240.0/20"]
   
   
   #Bastion Host
   aws_bastion_size = "t2.medium" // 베스쳔 호스트 인스턴스 타입
   
   
   #Kubernetes Cluster
   
   aws_kube_master_num  = 3	// 마스터노드 갯수
   aws_kube_master_size = "t2.medium"	// 마스터노드 인스턴스 타입
   
   aws_etcd_num  = 0			// etcd가 마스터 내부에 포함.		
   #aws_etcd_num  = 3				// etcd가 별도의 인스턴스에 생성됨. 이때 인스턴스 갯수
   aws_etcd_size = "t2.medium"		// etcd 인스턴스 타입
   
   aws_kube_worker_num  = 3		// worker노드 갯수
   aws_kube_worker_size = "t2.medium"		// worker 노드 인스턴스 타입
   
   #Settings AWS ELB
   
   aws_elb_api_port                = 6443
   k8s_secure_api_port             = 6443
   kube_insecure_apiserver_address = "0.0.0.0"
   
   default_tags = {
     #  Env = "devtest"
     #  Product = "kubernetes"
   }
   
   inventory_file = "../../../inventory/tmaxcloud/hosts"	// 결과 인벤토리 파일 경로
   ```
   
   - VPC는 한 리전당 생성 가능한 갯수 및 할당량이 존재하므로 적절히 고려하여 부여합니다.
   - Subnet 설정에서 리스트 안의 갯수를 늘리면 그에따라 여러 존에 Subnet을 생성하고 노드를 배포합니다. Ex) ["10.250.224.0/20", "10.250.240.0/20"]로 설정하면 2개의 존에 배포. 
   - `aws_etcd_num ` 값을 0으로 할 경우, etcd가 마스터에 포함되어 배포됩니다.
   - 인스턴스 유형의 정보는 [다음](https://aws.amazon.com/ko/ec2/instance-types/)을 참조합니다.
   
2. ami 설정

   variable.tf 파일을 열어 다음 부분을 찾습니다.

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

   사용하고자 하는 ami 정보를 해당 부분에 작성하여 저장합니다. 

   - AMI 정보 검색 방법
     1. AWS Console에 로그인하여 EC2로 접근합니다. 
     2. 탐색창에서 AMI를 선택합니다. 
     3. 필터를 적절하게 설정해 검색을 수행합니다.

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
   AWS_DEFAULT_REGION = "eu-central-1"  // 생성하고자 하는 리전명 
   ```

   - 키페어는 리전에 귀속되므로 다른 리전의 키페어를 입력하면 안됩니다. 생성하고자 하는 리전에 생성되어있는 키페어를 입력해야 합니다. 
   - 리전 명은 'ap-northeast-2' 와 같이 코드명으로 입력해야 합니다.

   credentials.tfvars 파일로 만든 후, `terraform init` 명령을 수행한 뒤   `terraform apply -var-file=credentials.tfvars` 명령을 수행하여 AWS에 인스턴스를 생성합니다.

2. kubespray의 이용

    `ansible-playbook -i ./inventory/hosts ./cluster.yml -e ansible_user=centos -b --become-user=root --flush-cache` 등의 명령을 통해 이용 가능합니다. aws 에서는 key 페어를 이용해야만 ssh로 접근가능하도록 하고 있기에 명령에 `ansible_ssh_private_key_file` 옵션을 추가해야 합니다.

   ```
   # 명령어 예시
   
   ansible-playbook -i ./inventory/tmaxcloud/hosts ./cluster.yml \
   -e ansible_user=centos \
   -e ansible_ssh_private_key_file=./your-key-pair.pem \
   -e cloud_provider=aws -b --become-user=root --flush-cache
   ```

   *<span style="color:gray">생성된 instance OS centos가 아닌 ubuntu 등의 경우 상단 ansible-playbook 명령의 ansible_user의 값이 OS 설정값에 맞게 바뀌어야 합니다. (ex- ubuntu라면  -e ansible_user=ubuntu)</span>* 

## Troubleshooting

### SSH 관련이슈

1. AWS에서의 보안 그룹, 네트워크ACL을 확인
   AWS-VPC-보안 탭의 네트워크ACL과 보안그룹의 Inbound/Outbound 규칙을 확인하여 필요로 하는 룰을 추가합니다.

2. Ansible-playbook 명령시 ssh permission error
   
   - ec2생성에 넣었던 키페어 파일의 권한을 확인합니다. (400 또는 600권장)
   - ansible 명령에서 keypire를 넣어주는 것이 아닌, .ssh에 .pem 파일을 넣고 ssh-add를 수행해 keypair가 시스템에 등록되도록 조치합니다.
   
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

## Remove

AWS resource들을 삭제해야 할 경우 `terraform destroy` 명령을 실행합니다. 

