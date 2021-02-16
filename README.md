# Smartcity Platform Lambda Functions

![Alt text](iot_component_diagram_new.png?raw=true "Smarcity Platform Component Diagram")

To package your function please run the following commands

`cd ~/MyFunctionName`

`zip -r  MyFunctionName.zip MyFunctionName.py greengrasssdk`

To create a new lambda function, run the following commands

`aws lambda create-function --function-name MyFunctionName --zip-file fileb://MyFunctionName.zip --handler MyFunctionName.function_handler --runtime python3.x  --role arn:aws:iam::MyFunctionName:role/lambda-ex`

To update the lambda function code, run the following command

`aws lambda update-function-code --function-name MyFunctionName --zip-file fileb://MyFunctionName.zip`