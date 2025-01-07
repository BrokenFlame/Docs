# AWS Secrets Manager 

## Binary Files upload
Note the use of "fileb://" at the start of the path

**Syntax**
```sh
aws secretsmanager put-secret-value --region AWSREGION --secret-id SECRETNAME  --secret-binary  fileb://FILEPATH 
```
**Example**
```sh
aws secretsmanager put-secret-value --region eu-west-2 --secret-id mySecret  --secret-binary  fileb:///config.json
```


## Binary Files download

Note "Version-Stage" can be either AWSPREVIOUS for the previous secret value or AWSCURRENT for the active secret value.

**Syntax**
```sh
aws secretsmanager get-secret-value --secret-id SECRETNAME --version-stage AWSPREVIOUS --region AWSREGION --query SecretBinary --output text | base64 --decode > OUTFILE
```

**Example**
```sh
aws secretsmanager get-secret-value --secret-id mySecret --version-stage AWSCURRENT --region eu-west-1 --query SecretBinary --output text | base64 --decode > certificate.p12
```
