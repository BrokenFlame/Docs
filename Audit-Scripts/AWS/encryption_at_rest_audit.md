Audit EC2 Instance Attached Drive Encryption

```sh
for instance in $(aws ec2 describe-instances \
  --region eu-west-2 \
  --query 'Reservations[].Instances[].InstanceId' \
  --output text); do

  aws ec2 describe-instances \
    --instance-ids "$instance" \
    --region eu-west-2 \
    --query 'Reservations[0].Instances[0].{InstanceId:InstanceId,Name:Tags[?Key==`Name`]|[0].Value}' \
    --output table

  for volume in $(aws ec2 describe-instances \
    --instance-ids "$instance" \
    --region eu-west-2 \
    --query 'Reservations[0].Instances[0].BlockDeviceMappings[].Ebs.VolumeId' \
    --output text); do
  
    aws ec2 describe-volumes \
      --volume-ids "$volume" \
      --region eu-west-2 \
      --query 'Volumes[0].{VolumeId:VolumeId,Encrypted:Encrypted,KMSKeyId:KmsKeyId,Size:Size,Type:VolumeType}' \
      --output table
  done
done
```
