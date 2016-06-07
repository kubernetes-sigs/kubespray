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

resource "aws_instance" "master" {
    count = "${var.numControllers}"
    ami = "${var.ami}"
    instance_type = "${var.master_instance_type}"
    subnet_id = "${var.subnet}"
    vpc_security_group_ids = ["${var.securityGroups}"]
    key_name = "${var.SSHKey}"
    disable_api_termination = "${var.terminate_protect}"
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
    root_block_device {
      volume_size = "${var.volSizeNodes}"
    }
    tags {
      Name = "${var.deploymentName}-minion-${count.index + 1}"
    }
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
