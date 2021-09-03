variable "name" {
  description = "Optional : The name parameter is used to name various components within the module."
  default="awsdynprefix"
}

variable "aws_lambda_function_memory_size" {
  description = "Optional : Amount of memory in MB your Lambda Function can use at runtime. Defaults to 128."
  default="128"
}

variable "aws_lambda_function_timeout" {
  description = "Optional : The amount of time your Lambda Function has to run in seconds. Defaults to 300."
  default="300"
}

variable "schedule_expression" {
  description = "Optional : The scheduling expression. For example, cron(0 20 * * ? *). The default is rate(5 minutes)."
  default="rate(5 minutes)"
}

variable "tags" {
  type = map(string)
  description = "Optional : A map of tags to assign to the resource."  
  default = { }
}

variable "variables" {
  type = map(string)
  description = "Required: A map of environment variables."  
  default = { }
}

variable "vpc_config" {
  type = map(list(string))
  description = "Optional: A map of subnet_ids and security_group_ids"  
  default = {
    subnet_ids         = []
    security_group_ids = []
  }
}

/*
  {
    debug = "true"
    test1 = "http://minemeld.dnb.com/feeds/s3"
    test2 = "http://minemeld.dnb.com/feeds/s3"
  }
*/