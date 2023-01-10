locals {
    buckets = { for x in ["gitpod"] : x => x }  
}

resource "random_string" "minio_username" {
  for_each = local.buckets

  length  = 16
  special = false
}

provider "minio" {
  minio_server     = "${var.STORAGE_HOSTNAME}:9000"
  minio_region     = "us-east-1"
  minio_access_key = var.MINIO_ACCESS_KEY
  minio_secret_key = var.MINIO_SECRET_KEY
}

resource "minio_s3_bucket" "state_terraform_s3" {
  for_each = local.buckets
  bucket   = each.key
}

resource "minio_iam_user" "user" {
  for_each = local.buckets

  name = random_string.minio_username[each.key].result
}

resource "minio_iam_policy" "readwrite" {
  for_each = local.buckets

  name = each.key
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = ["arn:aws:s3:::${each.key}"]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:*"]
        Resource = ["arn:aws:s3:::${each.key}", "arn:aws:s3:::${each.key}/*"]
      },
    ]
  })
}

resource "minio_iam_user_policy_attachment" "readwrite" {
  for_each = local.buckets

  user_name   = minio_iam_user.user[each.key].id
  policy_name = minio_iam_policy.readwrite[each.key].id
}
