# Simple script to enable S3 Version control on all the S3 Buckets in an account

for bucket in $(aws s3api list-buckets --query 'Buckets[].Name' --output text); do

    status=$(aws s3api get-bucket-versioning \
        --bucket "$bucket" \
        --query 'Status' \
        --output text)

    if [ "$status" = "Enabled" ]; then
        echo "[OK]      $bucket - already enabled"
    else
        echo "[ENABLE]  $bucket - current status: ${status:-NotEnabled}"

        aws s3api put-bucket-versioning \
            --bucket "$bucket" \
            --versioning-configuration Status=Enabled

        if [ $? -eq 0 ]; then
            echo "[SUCCESS] $bucket"
        else
            echo "[FAILED]  $bucket"
        fi
    fi

done
