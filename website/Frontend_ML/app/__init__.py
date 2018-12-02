from flask import Flask, render_template, request, jsonify, redirect
import json
import boto3
import imp
from ML import suggestion

app = Flask(__name__, static_folder='static')
sns = boto3.client('sns', region_name='us-east-1')
sug = ""

@app.route('/getResult', methods=['GET'])
def getResult():
    print "This is the result"
    global sug
    print sug
    return sug
    
@app.route('/sendSNS', methods=['GET', 'POST'])
def sendSNS():
    if request.method == 'POST':
        twitter_response = sns.publish(
            TopicArn='arn:aws:sns:us-east-1:441284944251:load-tweets',
            Message=json.dumps({
                "Records": [
                    {
                        "EventSource": "aws:sns",
                        "EventVersion": "1.0",
                        "EventSubscriptionArn": "arn:aws:sns:us-east-1:441284944251:load-tweets",
                        "Sns": {
                            "Type": "Notification",
                            "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                            "TopicArn": "arn:aws:sns:us-east-1:123456789012:ExampleTopic",
                            "Subject": "example subject",
                            "Message": {
                                "company": "Nike"
                            },
                            "Timestamp": "1970-01-01T00:00:00.000Z",
                            "SignatureVersion": "1",
                            "Signature": "EXAMPLE",
                            "SigningCertUrl": "EXAMPLE",
                            "UnsubscribeUrl": "EXAMPLE",
                            "MessageAttributes": {
                                "Test": {
                                    "Type": "String",
                                    "Value": "TestString"
                                },
                                "TestBinary": {
                                    "Type": "Binary",
                                    "Value": "TestBinary"
                                }
                            }
                        }
                    }
                ]
            })
        )
        if twitter_response['ResponseMetadata']['HTTPStatusCode'] != 200:
            print ("COMPANY NAME NOT SENT TO TWITTER LAMBDA")
            print twitter_response['ResponseMetadata']['HTTPStatusCode']
        company = request.form.get('name')
        global sug
        sug = suggestion.get_suggestion(company)
        print sug
        
    
    
    return render_template('index.html')

@app.route('/')
def hello():
    return render_template('index.html')