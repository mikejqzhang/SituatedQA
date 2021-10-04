import os
import json
import boto3
import argparse
from tqdm import tqdm
from collections import Counter

def format_question(question):
    question = question[0].upper() + question[1:]
    if question[-1] != '?':
        quesiton = question + '?'
    return question

def get_question_xml(args):
    with open(f'mturk/html/part_{args.part}.html', 'r') as f:
        html_layout = f.read()
        QUESTION_XML = """
        <HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
        <HTMLContent><![CDATA[{}]]></HTMLContent>
        <FrameHeight>650</FrameHeight>
        </HTMLQuestion>"""
        question_xml = QUESTION_XML.format(html_layout)
    return question_xml

def get_part_3_html_keys(hit_data):
    search_result_indent = '\n' + ' ' * 18
    search_result_template = '<span class="search-result dropdown-item" href="{link}" target="wikipedia-pane">{title}</span>'
    ann_articles = [{(article['link'], article['title'][:-12] if article['title'][-12:] == " - Wikipedia" else article['title'])
                     for article in ann['all_articles_used']}
                    for ann in hit_data['p2_annotations']]

    article_counts = Counter(article for ann in ann_articles for article in ann)
    all_search_results = [search_result_template.format(link=link, title=title)
                          for  (link, title), _ in article_counts.most_common()]
    search_results_html = search_result_indent + search_result_indent.join(all_search_results) + '\n'
    answer_template = """
          <div class="alert alert-primary my-2">
            <h5><b>Question:</b> {question}</h5>
            <br/>
            <h5><b>Response {answer_idx}:</b></h5>
            <ul>
              <li>
                <b>Current answer:</b>
                <p class="pl-4">{current_answer}</p>
              </li>
              <li>
                <b>Date when the current answer started to be true:</b>
                <p class="pl-4">{current_date}</p>
              </li>
              <li>
                <b>Previous answer:</b>
                <p class="pl-4">{previous_answer}</p>
              </li>
              <li>
                <b>Date when the previous answer started to be true:</b>
                <p class="pl-4">{previous_date}</p>
              </li>
            </ul>
            <hr/>
            <h5>Is this response correct?</h5>
            <div class="list-group list-group-horizontal">
              <label class="list-group-item list-group-item-success">
                <input class="form-check-input is_correct_input" name="isCorrect{answer_idx}" type="radio" value="Yes" autocomplete="off">
                Yes
              </label>
              <label class="list-group-item list-group-item-danger">
                <input class="form-check-input is_correct_input" name="isCorrect{answer_idx}" type="radio" value="No" autocomplete="off">
                No
              </label>
            </div>
          </div>"""
    answer_format_dicts = [{"question": hit_data['question'],
                            "current_answer": ann['cur_answer'] or 'N/A',
                            "current_date": ann['cur_answer_start'] or 'N/A',
                            "previous_answer": ann['prev_answer'] or 'N/A',
                            "previous_date": ann['prev_answer_start'] or 'N/A',
                            "answer_idx": i+1} for i, ann in enumerate(hit_data['p2_annotations'])]
    answers_html = '\n'.join([answer_template.format(**answer_dict) for answer_dict in answer_format_dicts]) + '\n'

    hit_keys = {
        '${QUESTION}': hit_data['question'],
        '${SEARCH_RESULTS}': search_results_html,
        '${ANSWERS}': answers_html,
    }
    return hit_keys


def get_client_preview(args):
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
    mturk_environment = (environments["production"]
                         if args.prod else environments["sandbox"])
    session = boto3.Session(profile_name=profile_name)
    client = session.client(
        service_name='mturk',
        region_name='us-east-1',
        endpoint_url=mturk_environment['endpoint'],
    )
    return client, mturk_environment['preview']

def get_task_attributes(args):
    with open('data/worker_quals.json', 'r') as f:
        worker_quals = json.load(f)
    good_qual_id = worker_quals[f'part_{args.part}_good']
    prev_qual_id = worker_quals[f'part_{args.part}_prev']

    if args.part == 1:
        task_title = "Has the answer to this question changed?"
        task_description = "Determine whether the answer to a question has changed over time."
    elif args.part == 2:
        task_title = "How has the answer to this question changed?"
        task_description = "Determine how the answer to a question has changed over time."
    elif args.part == 3:
        task_title = "Verify how the answer to this question has changed?"
        task_description = 'Compare and Verify responses to "How has the answer to this question changed?" 11111'
    elif args.part == 4:
        task_title = "Does the answer to this question change based on location?"
        task_description = "Determine whether the answer to a question depends on the asker's geographical location."
    elif args.part == 5:
        task_title = "How does the answer to this question change based on location?"
        task_description = "Determine answers "
    elif args.part == 6:
        print('ERROR')
        exit()
    else:
        print('ERROR')
        exit()
    
    if args.qual:
        task_title = task_title + " (Qualification Task)"
        task_description = task_description + " Complete this qualificaiton task for more!"
    else:
        task_description = task_description + " More to come! Search for our qualification task to participate!"
    qual_reqs = [
        # Locale
        {
            'QualificationTypeId': '00000000000000000071' ,
            'Comparator': 'EqualTo',
            'LocaleValues': [{'Country': 'US'}],
        },
        # Percent of HITs approved
            {
                'QualificationTypeId': '000000000000000000L0',
                'Comparator': 'GreaterThan',
                'IntegerValues': [95],
            }
    ]

    if args.prod:
        # Number of HITs approved
        qual_reqs.append({
            'QualificationTypeId': '00000000000000000040',
            'Comparator': 'GreaterThan',
            'IntegerValues': [1000],
        })
        if args.qual:
            # Has not previously tried the task
            qual_reqs.append({
                'QualificationTypeId': prev_qual_id,
                'Comparator': 'DoesNotExist',
            })
            # qual_reqs.append({
            #     'QualificationTypeId': '3R96LIPBRQ4C5WXT2DA53JQE0889FY',
            #     'Comparator': 'Exists',
            # })
        else:
            # Is good at the task
            qual_reqs.append({
                'QualificationTypeId': good_qual_id,
                'Comparator': 'Exists',
            })
    task_attributes = {
        'Title': task_title,
        'Description': task_description,
        'MaxAssignments': 0, # should be set later
        'LifetimeInSeconds': 60*60*args.n_hours,
        'AssignmentDurationInSeconds': 20*60,
        'Reward': args.reward,
        'Keywords': 'NLP,QA,Question,Answer',
        "QualificationRequirements": qual_reqs,
    }

    return task_attributes

def main(args):
    # Setting up Paths
    hit_jsons_path = f'data/part_{args.part}/hits_{args.version}.jsonl'
    task_dir = '{}/part_{}_{}'.format(
        'production' if args.prod else 'sandbox',
        args.part,
        args.version)
    print('New Task Dir:')
    print(task_dir)
    os.makedirs(task_dir, exist_ok=args.overwrite)

    # Loading Questions data
    with open(hit_jsons_path, 'r') as f:
        all_hit_jsons = [json.loads(l) for l in f]

    # Loading HIT Params:
    client, preview = get_client_preview(args)
    question_xml = get_question_xml(args)
    task_attributes = get_task_attributes(args)

    # Publishing HITs:
    hit_type_id = None
    publishing_stats = Counter()
    for hit_json in tqdm(all_hit_jsons):
        if len(hit_json['mturk_responses']) >= hit_json['n_way']:
            publishing_stats[0] += 1
            hit_id = None
        else:
            if args.part == 1:
                hit_keys = {'${' + f'QUESTION_{i}' + '}': format_question(hit_json['hit_data'][i]['question']) for i in range(5)}
            elif args.part == 2:
                hit_keys = {'${QUESTION}': format_question(hit_json['hit_data']['question'])}
            elif args.part == 3:
                hit_keys = get_part_3_html_keys(hit_json['hit_data'])
            elif args.part == 4:
                hit_keys = {'${' + f'QUESTION_{i}' + '}': format_question(hit_json['hit_data'][i]['question']) for i in range(5)}
            elif args.part == 5:
                hit_keys = {'${QUESTION}': format_question(hit_json['hit_data']['question']),
                            '${ORIGINAL_LOCATION}': hit_json['hit_data']['original_gpe'],
                            '${ORIGINAL_ANSWER}': '<ul><li>' + '</li><li>'.join(hit_json['hit_data']['original_answer']) + '</li></ul>'}
            else:
                print('ERROR')
                exit()
            
            hit_xml = question_xml
            for key, value in hit_keys.items():
                hit_xml = hit_xml.replace(key, value)

            task_attributes['MaxAssignments'] = hit_json['n_way'] - len(hit_json['mturk_responses'])
            response = client.create_hit(**task_attributes, Question=hit_xml)

            publishing_stats[task_attributes['MaxAssignments']] += 1
            hit_type_id = response['HIT']['HITTypeId']
            hit_id = response['HIT']['HITId']
        hit_json['hit_id'] = hit_id

    # Saving HITs
    with open(os.path.join(task_dir, 'published_hits.jsonl'), 'w') as f:
        for r in all_hit_jsons:
            f.write(json.dumps(r) + '\n')

    n_published_hits = sum(v for k, v in publishing_stats.items() if k!= 0)
    n_assignments = sum(k*v for k, v in publishing_stats.items())
    print('Published {} HITs w/ {} Assignments'.format(n_published_hits, n_assignments))
    print("You can view the HITs here:")
    print(preview+"?groupId={}".format(hit_type_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('--profile_name', type=str,
                        help='')
    parser.add_argument('--part', type=int,
                        help='')
    parser.add_argument('--version', type=str,
                        help='')
    parser.add_argument('--prod', action='store_true',
                        help='')
    parser.add_argument('--qual', action='store_true',
                        help='')
    parser.add_argument('--reward', type=str,
                        help='')
    parser.add_argument('--n_hours', type=int,
                        help='')
    parser.add_argument('--overwrite', action='store_true',
                        help='')
    args = parser.parse_args()
    assert args.part in [1, 2, 3, 4, 5]
    main(args)
