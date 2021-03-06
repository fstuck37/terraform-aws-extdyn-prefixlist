AWS Dynamic Prefix List
=============

This module deploys a Lambda function to create and maintain one or more prefix lists.
This is useful when you require IP addresses in a security group that change.
The URL requested needs to return a simple line delimited list of CIDR blocks.

Example
------------
```
module "awsdynprefix_useast1" {
  source  = "app.terraform.io/dnb-core/extdyn-prefixlist/aws"
  version = "0.0.1"
  name = "awsdynprefix_useast1"
  tags = var.tags
  schedule_expression = "rate(15 minutes)"
  variables =   {
    prefix = "siteshield=${module.SiteShield.lb_dns_name}"
  }
  vpc_config = [
    {
      subnet_ids         = ["subnet-1234567890abcdef12","subnet-123456789012abcdef","subnet-abcdef123456789012"]
      security_group_ids = [sg-123456789abcdefab]
    }
  ]
}
```
Information
------------
1. The number of entries allowed in the prefix list is limited by its usage. For example, if the prefix list is used in a security group this should be limited to the number of security group entries.
2. This code does not limit the size this should be controlled by the source URL.
3. This was tested with a feed from Palo Alto's Minemeld (https://github.com/PaloAltoNetworks/minemeld/wiki)

Argument Reference
------------
* **Settings**
   * **name** Optional : The name parameter is used to name various components within the module. Defaults to awsdynprefix.
   * **aws_lambda_function_memory_size** Optional : Amount of memory in MB your Lambda Function can use at runtime. Defaults to 128.
   * **aws_lambda_function_timeout** Optional : The amount of time your Lambda Function has to run in seconds. Defaults to 300.
   * **schedule_expression** Optional : The scheduling expression. For example, cron(0 20 * * ? *). The default is rate(5 minutes).
   * **tags** Optional : A map of tags to assign to the resource.
   * **variables** Required: A map of environment variables.
     * **debug** Optional: Boolean (True or False) to enable debug logging.
     * **prefix** Required: Semicolon(;) delimited list dictionary of prefix lists and URLs. "<name1>=<url1>;<name2>=<url2>;...;<nameN>=<urlN>"
     * **MaxEntries** Optional: Maximum number of prefix list entries. This defaults to 60 which matches the default limit on security group entries."
   ```
   {
     debug = "True"
     prefix = "http://test.example.com/feeds/s3"
     MaxEntries = "60"
   }
   ```
   * **vpc_config** Optional: A map of subnet_ids and security_group_ids
