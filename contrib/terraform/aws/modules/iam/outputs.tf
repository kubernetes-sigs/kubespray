output "kube-controlplane-profile" {
  value = aws_iam_instance_profile.kube-controlplane.name
}

output "kube-worker-profile" {
  value = aws_iam_instance_profile.kube-worker.name
}
