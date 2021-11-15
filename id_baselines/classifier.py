import os
import csv
import json
import argparse
from sklearn.metrics import precision_recall_fscore_support

import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments

class BinClassDataset(torch.utils.data.Dataset):
    def __init__(self, data, tokenizer):
        self.data = data
        texts = [ex['question'] for ex in data]
        self.encodings = tokenizer(texts, truncation=True, padding=True)
        self.label2idx = {'no': 0, 'yes': 1}
        if 'label' in data[0]:
            self.labels = [self.label2idx[ex['label']] for ex in data]
        else:
            self.labels = [0 for ex in data]
        
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)
        
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def load_data(data_paths, tokenizer):
    all_data = []
    for path in data_paths:
        with open(path, 'r') as f:
            all_data.extend(json.loads(l) for l in f)
    return BinClassDataset(all_data, tokenizer)

def train(args, model, tokenizer):
    train_dataset = load_data([args.train_path], tokenizer)
    dev_dataset = load_data([args.dev_path], tokenizer)
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=64,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=args.eval_steps,
        evaluation_strategy='epoch',
        load_best_model_at_end=True
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=dev_dataset,
        )
    trainer.train()
    model.save_pretrained(os.path.join(args.output_dir, 'best_checkpoint'))

def evaluate(args, model, tokenizer):
    preds_dataset = load_data([args.preds_path], tokenizer)
    training_args = TrainingArguments(
        output_dir=os.path.join(args.output_dir, 'tmp'), # this shouldn't be used
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=64,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=args.eval_steps,
        evaluation_strategy='steps',
        load_best_model_at_end=True
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=preds_dataset,
        eval_dataset=preds_dataset,
        )

    predictions = trainer.predict(preds_dataset)
    pred_labels = predictions[0].argmax(axis=1)
    gold_labels = predictions[1]
    pred_acc = (pred_labels == gold_labels).sum() / len(gold_labels)
    prfs_output  = precision_recall_fscore_support(gold_labels, pred_labels)
    p, r, fs, _ = [v[1] for v in prfs_output]

    print('a: {:.1f}'.format(pred_acc * 100))
    print('f: {:.1f}'.format(fs * 100))
    print('p: {:.1f}'.format(p * 100))
    print('r: {:.1f}'.format(r * 100))
    print('{:.1f} & {:.1f} & {:.1f} & {:.1f}'.format(pred_acc * 100, p * 100, r * 100, fs * 100,))

    preds_basename = os.path.split(args.preds_path)[1].rsplit('.', 1)[0]
    # metrics = {
    #         'dataset': preds_basename,
    #         'accuracy': pred_acc,
    #         'f1': ,
    #         }

    preds_path = os.path.join(
            args.output_dir, preds_basename + '.preds.jsonl')
    # metrics_path = os.path.join(
    #         args.output_dir, preds_basename + '.metrics.json')
    print(preds_path)
    with open(preds_path, 'w') as f:
        for ex, pred_label in zip(preds_dataset.data, pred_labels.tolist()):
            ex['pred_label'] = pred_label
            f.write(json.dumps(ex) + '\n')
    # print(metrics_path)
    # with open(metrics_path, 'w') as f:
    #     json.dump(metrics, f, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')

    # train args
    parser.add_argument('--experiment_name', type=str)
    parser.add_argument('--train_path', type=str)
    parser.add_argument('--dev_path', type=str)
    parser.add_argument('--task_dir', type=str)

    # shared args
    parser.add_argument('--saved_outputs_dir', type=str)
    parser.add_argument('--pretrained', type=str, default=None)
    parser.add_argument('--base_model', type=str, default=None)

    # eval args
    # parser.add_argument('--preds_path', type=str)
    parser.add_argument('--preds_path', type=str)

    # train hyperparameters
    parser.add_argument('--epochs', type=int,
                        default=10)
    parser.add_argument('--lr', type=float,
                        default=5e-5)
    parser.add_argument('--batch_size', type=int,
                        default=8)
    parser.add_argument('--eval_steps', type=int,
                        default=20)

    args = parser.parse_args()
    assert args.base_model in ['bert-base-uncased', 'bert-large-uncased']
    args.output_dir = os.path.join(args.saved_outputs_dir, args.task_dir, args.experiment_name)

    os.makedirs(args.output_dir, exist_ok=True)

    tokenizer = BertTokenizer.from_pretrained(args.base_model)
    model_checkpoint = args.pretrained or args.base_model
    model = BertForSequenceClassification.from_pretrained(model_checkpoint)

    if not args.pretrained:
        train(args, model, tokenizer)
    evaluate(args, model, tokenizer)


