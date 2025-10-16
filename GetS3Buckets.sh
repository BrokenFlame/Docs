REGION="eu-west-1"

echo "Name,Region,ARN,Website"

aws s3api list-buckets --query "Buckets[].Name" --output text | tr '\t' '\n' | while read BUCKET; do
  LOC=$(aws s3api get-bucket-location --bucket "$BUCKET" --query "LocationConstraint" --output text)
  LOC=${LOC:-us-east-1}

  if [ "$LOC" == "$REGION" ]; then
    ARN="arn:aws:s3:::$BUCKET"
    WEBSITE=$(aws s3api get-bucket-website --bucket "$BUCKET" 2>/dev/null \
      && echo "http://${BUCKET}.s3-website-${LOC}.amazonaws.com" \
      || echo "N/A")

    # Escape any commas in website field just in case
    WEBSITE_ESCAPED=$(echo "$WEBSITE" | sed 's/,//g')
    echo "\"$BUCKET\",\"$LOC\",\"$ARN\",\"$WEBSITE_ESCAPED\""
  fi
done
