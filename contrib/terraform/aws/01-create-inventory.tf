variable "SSHUser" {
  type = "string"
  description = "SSH User for VMs."
}

resource "null_resource" "ansible-provision" {

  depends_on = ["aws_instance.master","aws_instance.etcd","aws_instance.minion"]

  ##Create Master Inventory
  provisioner "local-exec" {
    command =  "echo \"[kube-master]\" > inventory"
  }
  provisioner "local-exec" {
    command =  "echo \"${join("\n",formatlist("%s ansible_ssh_user=%s", aws_instance.master.*.private_ip, var.SSHUser))}\" >> inventory"
  }

  ##Create ETCD Inventory
  provisioner "local-exec" {
    command =  "echo \"\n[etcd]\" >> inventory"
  }
  provisioner "local-exec" {
    command =  "echo \"${join("\n",formatlist("%s ansible_ssh_user=%s", aws_instance.etcd.*.private_ip, var.SSHUser))}\" >> inventory"
  }

  ##Create Nodes Inventory
  provisioner "local-exec" {
    command =  "echo \"\n[kube-node]\" >> inventory"
  }
  provisioner "local-exec" {
    command =  "echo \"${join("\n",formatlist("%s ansible_ssh_user=%s", aws_instance.minion.*.private_ip, var.SSHUser))}\" >> inventory"
  }

  provisioner "local-exec" {
    command =  "echo \"\n[k8s-cluster:children]\nkube-node\nkube-master\" >> inventory"
  }
}
