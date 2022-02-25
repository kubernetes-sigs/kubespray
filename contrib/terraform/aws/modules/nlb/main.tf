# Create a new AWS NLB for K8S API
resource "aws_lb" "aws-nlb-api" {
  name                             = "kubernetes-nlb-${var.aws_cluster_name}"
  load_balancer_type               = "network"
  subnets                          = length(var.aws_subnet_ids_public) <= length(var.aws_avail_zones) ? var.aws_subnet_ids_public : slice(var.aws_subnet_ids_public, 0, length(var.aws_avail_zones))
  idle_timeout                     = 400
  enable_cross_zone_load_balancing = true

  tags = merge(var.default_tags, tomap({
    Name = "kubernetes-${var.aws_cluster_name}-nlb-api"
  }))
}

# Create a new AWS NLB Instance Target Group
resource "aws_lb_target_group" "aws-nlb-api-tg" {
  name        = "kubernetes-nlb-tg-${var.aws_cluster_name}"
  port        = var.k8s_secure_api_port
  protocol    = "TCP"
  target_type = "ip"
  vpc_id      = var.aws_vpc_id

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
    protocol            = "HTTPS"
    path                = "/healthz"
  }
}

# Create a new AWS NLB Listener listen to target group
resource "aws_lb_listener" "aws-nlb-api-listener" {
  load_balancer_arn = aws_lb.aws-nlb-api.arn
  port              = var.aws_nlb_api_port
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.aws-nlb-api-tg.arn
  }
}
