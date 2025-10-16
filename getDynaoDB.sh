REGION="eu-west-1"   # Change to your AWS region
SERVICE="dynamodb"
ENDPOINT="https://${SERVICE}.${REGION}.amazonaws.com"

# Print CSV header
echo "Name,ARN,Endpoint"

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# List all DynamoDB tables
aws dynamodb list-tables --region "$REGION" --query "TableNames[]" --output text | tr '\t' '\n' | while read -r TABLE; do
    # Get table ARN
    ARN=$(aws dynamodb describe-table --table-name "$TABLE" --region "$REGION" --query "Table.TableArn" --output text 2>/dev/null)

    # Output CSV line
    echo "\"$TABLE\",\"$ARN\",\"$ENDPOINT\""
done
