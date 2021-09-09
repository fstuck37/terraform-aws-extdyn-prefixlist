AWS Dynamic Prefix List
=============

This module deploys a Lambda function to create and maintain one or more prefix lists.
This is useful when you require IP addresses in a security group that change.
The URL requested needs to return a simple line delimited list of CIDR blocks.

Example
------------
```

module "awsdynprefix" {
  source       = "git::https://github.com/fstuck37/terraform-aws-extdyn-prefixlist.git"

  tags = { 
    ProjectName    = "Infrastructure"
    Environment    = "Development"
    Classification = "Infrastructure"
  }

  schedule_expression = "rate(15 minutes)"
  
  variables =   {
    prefix = "test1=http://10.242.157.97/feeds/s3;test2=http://10.242.157.97/feeds/s3"
  }

  vpc_config = [
    {
      subnet_ids         = ["subnet-1a2b3c4d5e6f7a8b9, "subnet-123456789abcdefab", "subnet-12a34b56c78d90efa" ]
      security_group_ids = [sg-123456789abcdefab]
    }
  ]
}
```
Information
------------
1. The number of entries allowed in the prefix list is limited by its usage. For example, if the prefix list is used in a security group this should be limited to the number of security group entries.

Argument Reference
------------
* **Settings**
   * **name** Optional : The name parameter is used to name various components within the module. Defaults to awsdynprefix.
   * **aws_lambda_function_memory_size** Optional : Amount of memory in MB your Lambda Function can use at runtime. Defaults to 128.
   * **aws_lambda_function_timeout** Optional : The amount of time your Lambda Function has to run in seconds. Defaults to 300.
   * **schedule_expression** Optional : The scheduling expression. For example, cron(0 20 * * ? *). The default is rate(5 minutes).
   * **tags** Optional : A map of tags to assign to the resource.
   * **variables** Required: A map of environment variables.
   * **vpc_config** Optional: A map of subnet_ids and security_group_ids
	```
	{
	debug = "true"
	test1 = "http://test.example.com/feeds/s3"
	test2 = "http://test.example.com/feeds/s3"
	}
	```