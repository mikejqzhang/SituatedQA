import re
import json
import string
import argparse
import unicodedata
from collections import Counter


# Eval normalization from DrQA
def normalize(s):
    """Normalize answer."""
    s = unicodedata.normalize("NFD", s)
    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)
    def white_space_fix(text):
        return " ".join(text.split())
    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)
    def lower(text):
        return text.lower()
    s = white_space_fix(remove_articles(remove_punc(lower(s))))
    return s

def eval_geo(preds, data):
    loc_counter = Counter()
    for ex in data:
        for label in ex['context_answer_pairs']:
            loc_counter[normalize(label['location'])] += 1
    common_locations = [loc for loc, count in loc_counter.most_common()
                        if count >= 5]


    id2loc2ans = {ex['id']: {p['location']: [normalize(ans) for ans in p['answers']]
                for p in ex['context_answer_pairs']} for ex in data}

    em_counts = {'total': Counter(),
                 'common': Counter(),
                 'rare': Counter(),
                 'any': Counter()}

    for pred in preds:
        gold_answers = id2loc2ans[pred['id']][pred['context']]
        em_match = normalize(pred['pred_answer']) in gold_answers
        em_counts['total'][em_match] += 1
        if normalize(pred['context']) in common_locations:
            em_counts['common'][em_match] += 1
        else:
            em_counts['rare'][em_match] += 1
        any_answer = [a for loc in id2loc2ans[pred['id']].values() for a in loc]
        any_match = normalize(pred['pred_answer']) in any_answer
        em_counts['any'][any_match] += 1

    print('{}: {} / {} = {:.1f}'.format(
        'common',
        em_counts['common'][True],
        sum(em_counts['common'].values()),
        100 * em_counts['common'][True] / sum(em_counts['common'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'rare',
        em_counts['rare'][True],
        sum(em_counts['rare'].values()),
        100 * em_counts['rare'][True] / sum(em_counts['rare'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'total',
        em_counts['total'][True],
        sum(em_counts['total'].values()),
        100 * em_counts['total'][True] / sum(em_counts['total'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'any',
        em_counts['any'][True],
        sum(em_counts['any'].values()),
        100 * em_counts['any'][True] / sum(em_counts['any'].values())))

def eval_temp(preds, data):
    id2date2ans = {ex['id']: {p['date']: [normalize(ans) for ans in p['answers']]
                   for p in ex['context_answer_pairs']} for ex in data}
    id2date2type = {ex['id']: {p['date']: p['date_type']
                    for p in ex['context_answer_pairs']} for ex in data}

    em_counts = {'total': Counter(),
                 'static': Counter(),
                 'sampled': Counter(),
                 'start': Counter(),
                 'any': Counter()}

    for pred in preds:
        gold_answers = id2date2ans[pred['id']][pred['context']]
        date_type = id2date2type[pred['id']][pred['context']]
        em_match = normalize(pred['pred_answer']) in gold_answers
        if date_type == 'orig':
            em_counts['static'][em_match] += 1
        elif date_type == 'start':
            em_counts['start'][em_match] += 1
        else:
            em_counts['sampled'][em_match] += 1
        em_counts['total'][em_match] += 1
        any_answer = [a for date in id2date2ans[pred['id']].values() for a in date]
        any_match = normalize(pred['pred_answer']) in any_answer
        em_counts['any'][any_match] += 1

    print('{}: {} / {} = {:.1f}'.format(
        'static',
        em_counts['static'][True],
        sum(em_counts['static'].values()),
        100 * em_counts['static'][True] / sum(em_counts['static'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'sampled',
        em_counts['sampled'][True],
        sum(em_counts['sampled'].values()),
        100 * em_counts['sampled'][True] / sum(em_counts['sampled'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'start',
        em_counts['start'][True],
        sum(em_counts['start'].values()),
        100 * em_counts['start'][True] / sum(em_counts['start'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'total',
        em_counts['total'][True],
        sum(em_counts['total'].values()),
        100 * em_counts['total'][True] / sum(em_counts['total'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'any',
        em_counts['any'][True],
        sum(em_counts['any'].values()),
        100 * em_counts['any'][True] / sum(em_counts['any'].values())))

def eval_assumed_loc(preds, data):
    id2loc2ans = {ex['id']: {p['location']: [normalize(ans) for ans in p['answers']]
                for p in ex['context_answer_pairs']} for ex in data}

    em_counts = {common_locations[0]: Counter(),
                 common_locations[1]: Counter(),
                 'other': Counter(),
                 'rare': Counter()}

    for pred in preds:
        gold_answers = id2loc2ans[pred['id']][pred['context']]
        em_match = normalize(pred['pred_answer']) in gold_answers
        if normalize(pred['context']) == common_locations[0]:
            em_counts[common_locations[0]][em_match] += 1
        elif normalize(pred['context']) == common_locations[1]:
            em_counts[common_locations[1]][em_match] += 1
        elif normalize(pred['context']) in common_locations:
            em_counts['other'][em_match] += 1
        else:
            em_counts['rare'][em_match] += 1

    print('{}: {} / {} = {:.1f}'.format(
        common_locations[0],
        em_counts[common_locations[0]][True],
        sum(em_counts[common_locations[0]].values()),
        100 * em_counts[common_locations[0]][True] / sum(em_counts[common_locations[0]].values())))
    print('{}: {} / {} = {:.1f}'.format(
        common_locations[1],
        em_counts[common_locations[1]][True],
        sum(em_counts[common_locations[1]].values()),
        100 * em_counts[common_locations[1]][True] / sum(em_counts[common_locations[1]].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'other',
        em_counts['other'][True],
        sum(em_counts['other'].values()),
        100 * em_counts['other'][True] / sum(em_counts['other'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'rare',
        em_counts['rare'][True],
        sum(em_counts['rare'].values()),
        100 * em_counts['rare'][True] / sum(em_counts['rare'].values())))


def eval_cur_prev(preds, data):
    id2cur = {ex['id']: [normalize(ans) for ans in ex['cur_answers']] for ex in data}
    id2prev = {ex['id']: [normalize(ans) for ans in ex['prev_answers'] or []] for ex in data}

    em_counts = {'total': Counter(),
                 'cur': Counter(),
                 'prev': Counter(),
                 'any': Counter()}

    for pred in preds:
        if pred['context'] == 'cur':
            gold_answers = id2cur[pred['id']]
        else:
            gold_answers = id2prev[pred['id']]
        em_match = normalize(pred['pred_answer']) in gold_answers
        em_counts['total'][em_match] += 1
        if pred['context'] == 'cur':
            em_counts['cur'][em_match] += 1
        else:
            em_counts['prev'][em_match] += 1
        any_answer = id2cur[pred['id']] + id2prev[pred['id']]
        any_match = normalize(pred['pred_answer']) in any_answer
        em_counts['any'][any_match] += 1

    print('{}: {} / {} = {:.1f}'.format(
        'cur',
        em_counts['cur'][True],
        sum(em_counts['cur'].values()),
        100 * em_counts['cur'][True] / sum(em_counts['cur'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'prev',
        em_counts['prev'][True],
        sum(em_counts['prev'].values()),
        100 * em_counts['prev'][True] / sum(em_counts['prev'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'total',
        em_counts['total'][True],
        sum(em_counts['total'].values()),
        100 * em_counts['total'][True] / sum(em_counts['total'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'any',
        em_counts['any'][True],
        sum(em_counts['any'].values()),
        100 * em_counts['any'][True] / sum(em_counts['any'].values())))



def eval_cur_adapt(preds, data):
    id2ans = {ex['id']: [normalize(ans) for ans in ex['cur_answers']] for ex in data}

    id2updated = {}
    for ex in data:
        if ex['timelines'] == None:
            continue
        cur_starts = [tl['cur_start']['year'] for tl in ex['timelines'] if tl['cur_start']]
        if not cur_starts:
            continue
        id2updated[ex['id']] = min(cur_starts) > 2018

    em_counts = {'total': Counter(),
                 'stable': Counter(),
                 'updated': Counter()}

    for pred in preds:
        if pred['context'] == 'prev':
            continue
        gold_answers = id2ans[pred['id']]
        em_match = normalize(pred['pred_answer']) in gold_answers
        em_counts['total'][em_match] += 1
        if pred['id'] in id2updated and id2updated[pred['id']]:
            em_counts['updated'][em_match] += 1
        elif pred['id'] in id2updated :
            em_counts['stable'][em_match] += 1

    print('{}: {} / {} = {:.1f}'.format(
        'stable',
        em_counts['stable'][True],
        sum(em_counts['stable'].values()),
        100 * em_counts['stable'][True] / sum(em_counts['stable'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'updated',
        em_counts['updated'][True],
        sum(em_counts['updated'].values()),
        100 * em_counts['updated'][True] / sum(em_counts['updated'].values())))
    print('{}: {} / {} = {:.1f}'.format(
        'total',
        em_counts['total'][True],
        sum(em_counts['total'].values()),
        100 * em_counts['total'][True] / sum(em_counts['total'].values())))

def main(args):
    with open(args.data_path, 'r') as f:
        data = [json.loads(l) for l in f]
    with open(args.preds_path, 'r') as f:
        preds = [json.loads(l) for l in f]

    print('Evaluating', args.eval, 'on', args.preds_path)
    if args.eval == 'geo':
        eval_geo(preds, data)
    elif args.eval == 'temp':
        eval_temp(preds, data)
    elif args.eval == 'assumed_loc':
        eval_assumed_loc(preds, data)
    elif args.eval == 'cur_prev':
        eval_cur_prev(preds, data)
    elif args.eval == 'cur_adapt':
        eval_cur_adapt(preds, data)
    print('='*50)





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('--preds_path', type=str,
                        help='')
    parser.add_argument('--data_path', type=str,
                        help='')
    parser.add_argument('--eval', type=str,
                        help='')
    args = parser.parse_args()
    main(args)
