resource "aws_elb" "elb-masters" {
  name = "k8s-masters-elb"
  availability_zones = ["${split(",", var.av_zones)}"]

  listener {
    instance_port = 80
    instance_protocol = "http"
    lb_port = 80
    lb_protocol = "http"
  }

  health_check {
    healthy_threshold = 2
    unhealthy_threshold = 2
    timeout = 3
    target = "HTTP:80${var.masters.check}"
    interval = 30
  }

  cross_zone_load_balancing = true
  idle_timeout = 300
  connection_draining = true
  connection_draining_timeout = 300

  tags {
    Name = "elb-k8s-api"
  }
}
