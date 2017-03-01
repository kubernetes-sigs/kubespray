output "aws_vpc_id" {
    value = "${aws_vpc.cluster-vpc.id}"
}

output "aws_subnet_ids_private" {
    value = ["${aws_subnet.cluster-vpc-subnets-private.*.id}"]
}

output "aws_subnet_ids_public" {
    value = ["${aws_subnet.cluster-vpc-subnets-public.*.id}"]
}

output "aws_security_group" {
    value = ["${aws_security_group.kubernetes.*.id}"]

}
