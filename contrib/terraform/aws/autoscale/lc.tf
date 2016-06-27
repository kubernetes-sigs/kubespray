resource "aws_launch_configuration" "lc-masters" {
    name = "k8s-masters-lc"
    image_id = "${var.masters.ami}"
    instance_type = "${var.masters.type}"
    iam_instance_profile = "${aws_iam_instance_profile.masters.id}"
    key_name = "${var.masters.key}"
    security_groups = ["${var.masters.sg}"]

    lifecycle {
      create_before_destroy = true
    }
}

resource "aws_launch_configuration" "lc-etcd" {
    name = "k8s-etcd-lc"
    image_id = "${var.etcd.ami}"
    instance_type = "${var.etcd.type}"
    iam_instance_profile = "${aws_iam_instance_profile.etcd.id}"
    key_name = "${var.etcd.key}"
    security_groups = ["${var.etcd.sg}"]

    lifecycle {
      create_before_destroy = true
    }
}


resource "aws_launch_configuration" "lc-nodes" {
    name = "k8s-nodes-lc"
    image_id = "${var.nodes.ami}"
    instance_type = "${var.nodes.type}"
    iam_instance_profile = "${aws_iam_instance_profile.nodes.id}"
    key_name = "${var.nodes.key}"
    security_groups = ["${var.nodes.sg}"]

    lifecycle {
      create_before_destroy = true
    }
}
