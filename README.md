# hostregister

A Lambda written in python 3.7 that is triggered upon a new instance being created. Once the
instance is running, the Lambda will procure the necessary variables from the AWS account where it was deployed
and proceed to register the instance with Calico Enterprise™

## Deployment Instructions
Open the config.ini file and configure your cluster region, namespace and name
Afterwards, from the root of the project run the following instructions

```
pip3 install -r requirements.txt --target . --upgrade
zip -r9 ${OLDPWD}/function.zip .
```
the resulting function.zip function should be uploaded to AWS Lambda
### Alternative Deployment Instructions
Another option is to run the `prepare_lambda.sh` script that is included with the project. This shall copy the project
to the directory above `cwd`, install all dependencies, build a zip file for lambda in the `cwd` and then clean up
the temporary directory

## Configuration
your `config.ini` file has 2 sections.
[k8_cluster_section] and [instance_parameters_section]. The [k8_cluster_section] should have all the details about the
eks cluster you're using and the [instance_parameters_section] should contain fields `tag.key` and `tag.value` which
are optional, but which can be used to determine which instances should be registered by the lambda function.
If no filter tag exists in the [instance_parameters_section] section, the service should attempt to register all
ec2 instances that change state to running