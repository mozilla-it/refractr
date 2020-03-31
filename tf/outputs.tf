output "access_key" {
  value = module.ecr.ecr_iam_access_key
}

output "secret_access_key" {
  value = module.ecr.ecr_iam_secret_access_key
}
