import os
import csv
import json
import boto3
import argparse
import xmltodict
from tqdm import tqdm
from datetime import datetime
from collections import Counter

def get_client(args):
    profile_name = args.profile_name
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
    mturk_environment = environments["production"] if not args.sand else environments["sandbox"]
    session = boto3.Session(profile_name=profile_name)
    client = session.client(
        service_name='mturk',
        region_name='us-east-1',
        endpoint_url=mturk_environment['endpoint'],
    )
    return client

def main(args):
    # Loading published HIT data
    task_dir = f'production/part_{args.part}_{args.version}' if not args.sand else f'sandbox/part_{args.part}_{args.version}'
    with open(os.path.join(task_dir, 'published_hits.jsonl'), 'r') as f:
        all_pub_data = [json.loads(l) for l in f]

    client = get_client(args)

    # Reading HIT data
    hit_counter = Counter()
    hit_status_counter = Counter()
    for pub_hit in tqdm(all_pub_data):
        if pub_hit['hit_id'] == None:
            continue
        else:
            # Getting HIT Assignments
            hit = client.get_hit(HITId=pub_hit['hit_id'])
            assignmentsList = client.list_assignments_for_hit(
                HITId=pub_hit['hit_id'],
                AssignmentStatuses=['Submitted', 'Approved'],
                MaxResults=hit['HIT']['MaxAssignments']
            )
            assignments = assignmentsList['Assignments']

            # Reading HIT Responses
            for assignment in assignments:
                worker_id = assignment['WorkerId']
                assignment_id = assignment['AssignmentId']
                answer_dict = xmltodict.parse(assignment['Answer'])
                answer = {field["QuestionIdentifier"]: field["FreeText"]
                          for field in answer_dict['QuestionFormAnswers']['Answer']}
                # Add the answers that have been retrieved for this item
                response = json.loads(answer['answerData'])
                pub_hit['mturk_responses'].append(response)

                # Approve the Assignment (if it hasn't been already)
                if assignment['AssignmentStatus'] == 'Submitted':
                    hit_counter['new'] += 1
                    if args.approve:
                        hit_counter['approved'] += 1
                        client.approve_assignment(
                            AssignmentId=assignment_id,
                            OverrideRejection=False)
                else:
                    hit_counter['approved'] += 1

            # Delete the hit if asked to
            hit_status_counter[hit['HIT']['HITStatus']] += 1
            if hit['HIT']['HITStatus'] == 'Reviewable':
                hit_counter['can_delete'] += 1
                if args.delete:
                    client.delete_hit(HITId=pub_hit['hit_id'])
            elif hit['HIT']['HITStatus'] == 'Assignable':
                hit_counter['can_delete'] += 1
                if args.delete:
                    client.update_expiration_for_hit(
                        HITId=pub_hit['hit_id'],
                        ExpireAt=datetime(2015, 1, 1)
                    )
            else:
                hit_counter['cant_delete'] += 1

    # Printing HIT status
    print('HIT status counts:')
    for k, v in hit_status_counter.items():
        print('\t', k, v)
    print('='*60)
    print('New Submissions Count:' , hit_counter['new'])
    print('Approved Submissions Count:' , hit_counter['approved'])
    print('N Can Delete:' , hit_counter['can_delete'])
    print('N Cant Delete:' , hit_counter['cant_delete'])

    # Printing HIT data
    with open(os.path.join(task_dir, 'mturk_outputs.jsonl'), 'w') as f:
        for response in all_pub_data:
            del response['hit_id']
            f.write(json.dumps(response) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('--profile_name', type=str,
                        help='')
    parser.add_argument('--part', type=int,
                        help='')
    parser.add_argument('--version', type=str,
                        help='')
    parser.add_argument('--sand', action='store_true',
                        help='')
    parser.add_argument('--delete', action='store_true',
                        help='')
    parser.add_argument('--approve', action='store_true',
                        help='')
    args = parser.parse_args()
    assert args.part in [1, 2, 3, 4, 5]
    main(args)
