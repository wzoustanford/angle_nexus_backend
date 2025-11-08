"""
DynamoDB Table Creation Script for UserSubscriptions
Run this once to create the subscription table
"""
import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

def create_subscription_table():
    """Create the UserSubscriptions table in DynamoDB"""
    try:
        dynamodb = boto3.client(
            'dynamodb',
            region_name=os.getenv('AWS_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        table_name = 'UserSubscriptions'
        
        # Check if table already exists
        try:
            response = dynamodb.describe_table(TableName=table_name)
            print(f"✓ Table '{table_name}' already exists")
            print(f"  Status: {response['Table']['TableStatus']}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
        # Create table
        print(f"Creating table '{table_name}'...")
        
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'user_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'platform',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'  # String
                },
                {
                    'AttributeName': 'platform',
                    'AttributeType': 'S'  # String
                }
            ],
            BillingMode='PAY_PER_REQUEST',  # On-demand billing
            Tags=[
                {
                    'Key': 'Application',
                    'Value': 'Angle'
                },
                {
                    'Key': 'Purpose',
                    'Value': 'Subscription Management'
                }
            ]
        )
        
        # Wait for table to be created
        print("Waiting for table to be created...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"✓ Table '{table_name}' created successfully!")
        print(f"  ARN: {response['TableDescription']['TableArn']}")
        
        return True
        
    except ClientError as e:
        print(f"✗ Error creating table: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Angle Finance - DynamoDB Subscription Table Setup")
    print("=" * 60)
    print()
    
    if create_subscription_table():
        print()
        print("✓ Setup completed successfully!")
        print()
        print("Table Schema:")
        print("  - Partition Key: user_id (String)")
        print("  - Sort Key: platform (String)")
        print("  - Billing Mode: On-demand (PAY_PER_REQUEST)")
    else:
        print()
        print("✗ Setup failed. Please check your AWS credentials and try again.")
