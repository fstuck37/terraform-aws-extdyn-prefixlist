resource "aws_iam_role" "awsdynprefix" {
  name = var.name
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "awsdynprefix" {
  name = var.name
  role = aws_iam_role.awsdynprefix.name

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "ec2:Describe*",
	        "ec2:CreateManagedPrefixList",
                "ec2:DeleteManagedPrefixList",
                "ec2:ModifyManagedPrefixList",
                "ec2:GetManagedPrefixListEntries",
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_lambda_function" "awsdynprefix" {
  filename         = "${path.module}/awsdynprefix.zip"
  source_code_hash = filebase64sha256("${path.module}/awsdynprefix.zip")
  function_name    = var.name
  description      = "Lambda Function to create and update dynamic prefix lists"
  role             = aws_iam_role.awsdynprefix.arn
  memory_size	   = var.aws_lambda_function_memory_size
  timeout      	   = var.aws_lambda_function_timeout
  handler          = "awsdynprefix.lambda_handler"
  runtime          = "python3.7"


  dynamic "vpc_config" {
    for_each = var.vpc_config
    content {
      subnet_ids = vpc_config.value["subnet_ids"]
      security_group_ids = vpc_config.value["security_group_ids"]
    }
  }

  environment {
    variables = var.variables
  }

  tags = var.tags
}

resource "aws_lambda_permission" "allow_cloudwatch_events" {
  statement_id   = "AllowExecutionFromCloudWatchEvents"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.awsdynprefix.function_name
  principal      = "events.amazonaws.com"
  source_arn     = aws_cloudwatch_event_rule.awsdynprefix.arn
}

resource "aws_cloudwatch_event_rule" "awsdynprefix" {
  name        = var.name
  description = "This is a rule for triggering our lambdas every five minutes."
  schedule_expression = var.schedule_expression
}
  
resource "aws_cloudwatch_event_target" "awsdynprefix" {
  rule      = aws_cloudwatch_event_rule.awsdynprefix.name
  arn       = aws_lambda_function.awsdynprefix.arn
}
