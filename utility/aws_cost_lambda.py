import json
import boto3
import os
import urllib3
from datetime import datetime, date, time, timedelta

client = boto3.client('ce', region_name='ap-southeast-1')
http = urllib3.PoolManager()
today = date.today()
current_day = today.replace(day=1)

# to retrieve (current month - 2) i.e Oct
prev_month = (current_day - timedelta(days=30*2)).replace(day=1)

SLACK_WEBHOOK_URL = ''
# enter your aws account id. If you have multiple accounts put all account ids.
AWS_ACCOUNT_ID = ['{Your AWS account}']

# to retrieve last day of the current_month
def last_day_of_month(any_day):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - timedelta(days=next_month.day)

# first day of Oct since we will be fetching 1 Quarter of cost
START_DATE = str(prev_month)  

# last day of Dec - current month
END_DATE = str(last_day_of_month(date(current_day.year, current_day.month, 1))) 

# if you have tags specific services
tags_=[("PROD","prod")]

# report generation 
def report(COST,account_id,acc_name,tags):    
    # TIME - start
    print(COST['ResultsByTime'][0]['TimePeriod']['Start'])
    time_period_start1= COST['ResultsByTime'][0]['TimePeriod']['Start']
    time_period_start2= COST['ResultsByTime'][1]['TimePeriod']['Start']
    time_period_start3= COST['ResultsByTime'][2]['TimePeriod']['Start']

    # TIME - end
    time_period_end1= COST['ResultsByTime'][0]['TimePeriod']['End']
    time_period_end2= COST['ResultsByTime'][1]['TimePeriod']['End']
    time_period_end3= COST['ResultsByTime'][2]['TimePeriod']['End']

    # checking if we receive any response
    try:
        res1=''
        res2=''
        res3=''
        t1=COST['ResultsByTime'][0]
        t2=COST['ResultsByTime'][1]
        t3=COST['ResultsByTime'][2]
        k1=[]
        a1=[]
        # for first time-period
        try:
            t1=COST['ResultsByTime'][0]
            tp1_key=t1['Groups'][0]['Keys']
            for i in range(0,len(t1['Groups'])):
                tp1_key=t1['Groups'][i]['Keys']
                tp1_key = str(tp1_key).strip("['']")
                k1.append(tp1_key)
                tp1_amount=t1['Groups'][i]['Metrics']['UnblendedCost']['Amount']
                a1.append(tp1_amount)
            a1=map(float, a1)
            a1= [round(item,3) for item in a1]
            res1 = dict(zip(k1, a1))
            suma1=round(sum(a1),4)
            res1 = str(res1) + " *Total* :moneybag: = " + str(suma1)
        except (KeyError, IndexError):
            suma1 = 0
            res1 = ''

        # for second time-period
        k2=[]
        a2=[]
        try:          
            t2=COST['ResultsByTime'][1]
            tp2_key=t2['Groups'][0]['Keys'] 
            for i in range(0,len(t2['Groups'])):
                tp2_key=t2['Groups'][i]['Keys']
                tp2_key = str(tp2_key).strip("['']")
                k2.append(tp2_key)
                tp2_amount=t2['Groups'][i]['Metrics']['UnblendedCost']['Amount']
                a2.append(tp2_amount)
            a2=map(float, a2)
            a2= [round(item,3) for item in a2]
            res2 = dict(zip(k2, a2))
            suma2=round(sum(a2),4)
            res2 = str(res2) + " *Total* :moneybag: = " + str(suma2)
        except (KeyError, IndexError):
            suma2 = 0
            res2 = ''

        # for third time-period
        res3=''
        k3=[]
        a3=[]
        try:
            t3=COST['ResultsByTime'][2]
            tp3_key=t3['Groups'][0]['Keys']
            for i in range(0,len(t3['Groups'])):
                tp3_key= t3['Groups'][i]['Keys']
                tp3_key = str(tp3_key).strip("['']")
                k3.append(tp3_key)
                print("appending ",tp3_key,k3)
                tp3_amount= t3['Groups'][i]['Metrics']['UnblendedCost']['Amount']
                a3.append(tp3_amount)
            a3=map(float, a3)
            a3= [round(item,4) for item in a3]
            res3 = dict(zip(k3, a3))
            suma3=round(sum(a3),4)
            res3 = str(res3) + " *Total* :moneybag: = " + str(suma3)
        except (KeyError, IndexError):
            suma3 = 0
            res3 = ''

    except (KeyError, IndexError):
        total = 0
        suma1=0
        suma2=0
        suma3=0
        
    total = round(suma1+suma2+suma3,5)
    

    UNIT = "SGD" 
    
    # add the channel name
    channel="#labs-aws-cost"
    
    tags_str = str(tags).split(", ")[0].strip("('')")
    
    # slack format where you can add formatting to slack message
    SLACK_MESSAGE={
        "channel": channel,

                        "username": "AWS Cost Monitor",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your AWS account {account_id} - {acc_name} ({tags_str}) Time period - {START_DATE} to {END_DATE} :aws: \n $ TOTAL = {total}  :moneybag: \n"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Service:* * Total Cost ({time_period_start1} to {time_period_end1}):* {res1} :moneybag: \n"
                }
            },
                        {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Service:* * Total Cost ({time_period_start2} to {time_period_end2}):* {res2} :moneybag: \n"
                }
            },
                        {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Service:* * Total Cost ({time_period_start3} to {time_period_end3}):* {res3} :moneybag: \n"
                }
            },

            {
                "type": "divider"
            }
        ]

    }
    return SLACK_MESSAGE

def call_api(account_id,tags):
    # call describe_account to retrieve the account name
    acc_name =   boto3.client('organizations').describe_account(AccountId=account_id).get('Account').get('Name')

    # call get_cost_and_usage boto3 function to retrieve the cost incurred 
    # for all services with matching tag values
    # you can provide the granularity to daily/monthly as required

    COST = client.get_cost_and_usage( 
                TimePeriod = {'Start': START_DATE, 'End':END_DATE},

                Granularity = 'MONTHLY',

                Metrics = ['UnblendedCost'],
        GroupBy= [
                    {
                    "Type": "DIMENSION",
                    "Key": "SERVICE"
                    }
                ],
        Filter = {
    "And":[{"Dimensions": { "Key": "LINKED_ACCOUNT", "Values": [account_id] }},
    {"Tags": { "Key": "environment", "Values": tags }} ]
    }                

    )

    print(COST)

    SLACK_MESSAGE = report(COST,account_id,acc_name,tags)
    return SLACK_MESSAGE
for i in range(0,len(AWS_ACCOUNT_ID)):
    print("##",AWS_ACCOUNT_ID[i],tags_[i])
    SLACK_MESSAGE = call_api(AWS_ACCOUNT_ID[i],tags_[i])
    ENCODED_SLACK_MESSAGE= json.dumps(SLACK_MESSAGE).encode('utf-8')
    SLACK_RESPONSE = http.urlopen ("POST",SLACK_WEBHOOK_URL, body=ENCODED_SLACK_MESSAGE)
    print(SLACK_RESPONSE.data)å