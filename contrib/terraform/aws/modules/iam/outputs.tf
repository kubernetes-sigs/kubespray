output "kube_control_plane-profile" {
  value = aws_iam_instance_profile.kube_control_plane.name
}

output "kube-worker-profile" {
  value = aws_iam_instance_profile.kube-worker.name
}
