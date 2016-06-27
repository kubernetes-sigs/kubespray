variable "deploymentName" {
  type = "string"
  description = "The desired name of your deployment."
}

variable "numControllers"{
  type = "string"
  description = "Desired # of controllers."
}

variable "numEtcd" {
  type = "string"
  description = "Desired # of etcd nodes. Should be an odd number."
}

variable "numNodes" {
  type = "string"
  description = "Desired # of nodes."
}

variable "volSizeController" {
  type = "string"
  description = "Volume size for the controllers (GB)."
}

variable "volSizeEtcd" {
  type = "string"
  description = "Volume size for etcd (GB)."
}

variable "volSizeNodes" {
  type = "string"
  description = "Volume size for nodes (GB)."
}

variable "subnet" {
  type = "string"
  description = "The subnet in which to put your cluster."
}

variable "securityGroups" {
  type = "string"
  description = "The sec. groups in which to put your cluster."
}

variable "ami"{
  type = "string"
  description = "AMI to use for all VMs in cluster."
}

variable "SSHKey" {
  type = "string"
  description = "SSH key to use for VMs."
}

variable "master_instance_type" {
  type = "string"
  description = "Size of VM to use for masters."
}

variable "etcd_instance_type" {
  type = "string"
  description = "Size of VM to use for etcd."
}

variable "node_instance_type" {
  type = "string"
  description = "Size of VM to use for nodes."
}

variable "terminate_protect" {
  type = "string"
  default = "false"
}

variable "awsRegion" {
  type = "string"
}

provider "aws" {
  region = "${var.awsRegion}"
}

variable "iam_prefix" {
  type = "string"
  description = "Prefix name for IAM profiles"
}

resource "aws_iam_instance_profile" "kubernetes_master_profile" {
  name = "${var.iam_prefix}_kubernetes_master_profile"
  roles = ["${aws_iam_role.kubernetes_master_role.name}"]
}

resource "aws_iam_role" "kubernetes_master_role" {
  name = "${var.iam_prefix}_kubernetes_master_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "kubernetes_master_policy" {
    name = "${var.iam_prefix}_kubernetes_master_policy"
    role = "${aws_iam_role.kubernetes_master_role.id}"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ec2:*"],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": ["elasticloadbalancing:*"],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "kubernetes_node_profile" {
  name = "${var.iam_prefix}_kubernetes_node_profile"
  roles = ["${aws_iam_role.kubernetes_node_role.name}"]
}

resource "aws_iam_role" "kubernetes_node_role" {
  name = "${var.iam_prefix}_kubernetes_node_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "kubernetes_node_policy" {
    name = "${var.iam_prefix}_kubernetes_node_policy"
    role = "${aws_iam_role.kubernetes_node_role.id}"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "ec2:Describe*",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "ec2:AttachVolume",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "ec2:DetachVolume",
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_instance" "master" {
    count = "${var.numControllers}"
    ami = "${var.ami}"
    instance_type = "${var.master_instance_type}"
    subnet_id = "${var.subnet}"
    vpc_security_group_ids = ["${var.securityGroups}"]
    key_name = "${var.SSHKey}"
    disable_api_termination = "${var.terminate_protect}"
    iam_instance_profile = "${aws_iam_instance_profile.kubernetes_master_profile.id}"
    root_block_device {
      volume_size = "${var.volSizeController}"
    }
    tags {
      Name = "${var.deploymentName}-master-${count.index + 1}"
    }
}

resource "aws_instance" "etcd" {
    count = "${var.numEtcd}"
    ami = "${var.ami}"
    instance_type = "${var.etcd_instance_type}"
    subnet_id = "${var.subnet}"
    vpc_security_group_ids = ["${var.securityGroups}"]
    key_name = "${var.SSHKey}"
    disable_api_termination = "${var.terminate_protect}"
    root_block_device {
      volume_size = "${var.volSizeEtcd}"
    }
    tags {
      Name = "${var.deploymentName}-etcd-${count.index + 1}"
    }
}


resource "aws_instance" "minion" {
    count = "${var.numNodes}"
    ami = "${var.ami}"
    instance_type = "${var.node_instance_type}"
    subnet_id = "${var.subnet}"
    vpc_security_group_ids = ["${var.securityGroups}"]
    key_name = "${var.SSHKey}"
    disable_api_termination = "${var.terminate_protect}"
    iam_instance_profile = "${aws_iam_instance_profile.kubernetes_node_profile.id}"
    root_block_device {
      volume_size = "${var.volSizeNodes}"
    }
    tags {
      Name = "${var.deploymentName}-minion-${count.index + 1}"
    }
}

output "kubernetes_master_profile" {
  value = "${aws_iam_instance_profile.kubernetes_master_profile.id}"
}

output "kubernetes_node_profile" {
  value = "${aws_iam_instance_profile.kubernetes_node_profile.id}"
}

output "master-ip" {
    value = "${join(", ", aws_instance.master.*.private_ip)}"
}

output "etcd-ip" {
    value = "${join(", ", aws_instance.etcd.*.private_ip)}"
}

output "minion-ip" {
    value = "${join(", ", aws_instance.minion.*.private_ip)}"
}


