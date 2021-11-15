
import json
import argparse

def main(args):
    for split in ['train', 'dev']:
        with open(f'qa_data/temp.{split}.jsonl', 'r') as f:
            raw_data = [json.loads(l) for l in f]
        pre_split = []
        post_split = []
        for ex in raw_data:
            if not ex['timelines']:
                continue
            start_dates = [tl['cur_start']['year'] for tl in ex['timelines'] if tl['cur_start']]
            if not start_dates:
                continue
            if min(d >= args.year for d in start_dates):
                post_split.append(ex)
            else:
                pre_split.append(ex)

        with open(f'temp_splits/pre_{args.year}.{split}.jsonl', 'w') as f:
            for ex in pre_split:
                f.write(json.dumps({'question': ex['question'],
                                    'id': ex['id'],
                                    'answer': ex['cur_answers']}) + '\n')
        with open(f'temp_splits/post_{args.year}.{split}.jsonl', 'w') as f:
            for ex in post_split:
                f.write(json.dumps({'question': ex['question'],
                                    'id': ex['id'],
                                    'answer': ex['cur_answers']}) + '\n')




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split current answers on a given year')
    parser.add_argument('--year', type=int, default=2019,
                        help='year where current answer start date is from < year or >= year')
    args = parser.parse_args()
    main(args)
