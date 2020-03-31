provider "aws" {
  region = "us-west-2"
}

module "ecr" {
  source = "github.com/mozilla-it/terraform-modules//aws/ecr?ref=master"
  repo_name = "refractr"
}
