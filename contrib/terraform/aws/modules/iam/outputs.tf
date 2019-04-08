output "kube-master-profile" {
  value = "${aws_iam_instance_profile.kube-master.name }"
}

output "kube-worker-profile" {
  value = "${aws_iam_instance_profile.kube-worker.name }"
}
