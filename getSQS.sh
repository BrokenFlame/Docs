REGION="eu-west-2"

# Print CSV header
echo "Name,ARN,Endpoint"

# List all queues in the region
aws sqs list-queues --region "$REGION" --query "QueueUrls[]" --output text | tr '\t' '\n' | while read QUEUE_URL; do
    # Extract the queue name from the URL (the last part)
    NAME=$(basename "$QUEUE_URL")
    ARN="arn:aws:sqs:$REGION:$(aws sts get-caller-identity --query Account --output text):$NAME"
    ENDPOINT="$QUEUE_URL"
    
    # Output CSV line
    echo "\"$NAME\",\"$ARN\",\"$ENDPOINT\""
done
