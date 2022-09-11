import json

import feedgen

def lambda_handler(evt: dict, ctx: dict):
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
