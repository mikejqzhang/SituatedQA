import os
import json
import boto3
import argparse
from tqdm import tqdm
from collections import Counter

def get_client():
    profile_name = 'parlai_mturk'
    environments = {
        "production": {
            "endpoint": "https://mturk-requester.us-east-1.amazonaws.com",
            "preview": "https://www.mturk.com/mturk/preview"
        },
        "sandbox": {
            "endpoint": "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
            "preview": "https://workersandbox.mturk.com/mturk/preview"
        },
    }
    mturk_environment = environments["production"]
    session = boto3.Session(profile_name=profile_name)
    client = session.client(
        service_name='mturk',
        region_name='us-east-1',
        endpoint_url=mturk_environment['endpoint'],
    )
    return client

def main(args):
    with open('data/worker_quals.json', 'r') as f:
        worker_quals = json.load(f)
    good_qual_id = worker_quals[f'part_{args.part}_good']
    good_workers = worker_quals[f'part_{args.part}_good_worker_ids']
    prev_qual_id = worker_quals[f'part_{args.part}_prev']
    prev_workers = worker_quals[f'part_{args.part}_prev_worker_ids']
    client = get_client()

    if args.remove:
        response = client.disassociate_qualification_from_worker(
            WorkerId=args.remove,
            QualificationTypeId=good_qual_id,
            Reason='Quality standards.'
        )
    else:
        for worker_id in tqdm(good_workers):
            response = client.associate_qualification_with_worker(
                QualificationTypeId=good_qual_id,
                WorkerId=worker_id,
                IntegerValue=1,
                SendNotification=True
            )
        for worker_id in tqdm(prev_workers):
            response = client.associate_qualification_with_worker(
                QualificationTypeId=prev_qual_id,
                WorkerId=worker_id,
                IntegerValue=1,
                SendNotification=False
            )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('--part', type=int)
    parser.add_argument('--remove', type=str, default=None)
    args = parser.parse_args()
    main(args)

    # client = get_client()
    # response = client.associate_qualification_with_worker(
    #     QualificationTypeId='3R96LIPBRQ4C5WXT2DA53JQE0889FY',
    #     WorkerId='AYIFHDQSXQJ6B',
    #     IntegerValue=1,
    #     SendNotification=True
    # )
