resource "aws_autoscaling_group" "masters" {
  availability_zones = ["${split(",", var.av_zones)}"]
  vpc_zone_identifier = ["${split(",", var.masters.subnets)}"]
  name = "k8s-as-masters"
  max_size = 2
  min_size = 2
  desired_capacity = 2
  health_check_grace_period = 300
  health_check_type = "ELB"
  launch_configuration = "${aws_launch_configuration.lc-masters.name}"
  load_balancers = ["${aws_elb.elb-masters.name}"]

  tag {
    key = "Name"
    value = "k8s-master"
    propagate_at_launch = true
  }
  tag {
    key = "role"
    value = "master"
    propagate_at_launch = true
  }
  tag {
    key = "env"
    value = "${var.env}"
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_group" "etcd" {
  availability_zones = ["${split(",", var.av_zones)}"]
  vpc_zone_identifier = ["${split(",", var.nodes.subnets)}"]
  name = "k8s-as-etcd"
  max_size = 3
  min_size = 3
  desired_capacity = 3
  health_check_type = "EC2"
  health_check_grace_period = 300
  launch_configuration = "${aws_launch_configuration.lc-etcd.name}"

  tag {
    key = "Name"
    value = "k8s-etcd"
    propagate_at_launch = true
  }
  tag {
    key = "role"
    value = "etcd"
    propagate_at_launch = true
  }
  tag {
    key = "env"
    value = "${var.env}"
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_group" "nodes" {
  availability_zones = ["${split(",", var.av_zones)}"]
  vpc_zone_identifier = ["${split(",", var.nodes.subnets)}"]
  name = "k8s-as-nodes"
  max_size = 10
  min_size = 2
  desired_capacity = 3
  health_check_grace_period = 300
  health_check_type = "ELB"
  launch_configuration = "${aws_launch_configuration.lc-nodes.name}"

  tag {
    key = "Name"
    value = "k8s-node"
    propagate_at_launch = true
  }
  tag {
    key = "role"
    value = "node"
    propagate_at_launch = true
  }
  tag {
    key = "env"
    value = "${var.env}"
    propagate_at_launch = true
  }
}
