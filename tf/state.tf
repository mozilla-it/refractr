terraform {
  backend "s3" {
    bucket         = "itsre-state-783633885093"
    key            = "us-west-2/refractr/ecr.tfstate"
    dynamodb_table = "itsre-state-783633885093"
    region         = "eu-west-1"
  }
}
