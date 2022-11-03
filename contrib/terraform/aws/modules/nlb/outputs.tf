output "aws_nlb_api_id" {
  value = aws_lb.aws-nlb-api.id
}

output "aws_nlb_api_fqdn" {
  value = aws_lb.aws-nlb-api.dns_name
}

output "aws_nlb_api_tg_arn" {
  value = aws_lb_target_group.aws-nlb-api-tg.arn
}
