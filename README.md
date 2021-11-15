# SituatedQA

[**Datasets/Tasks**](https://github.com/mikejqzhang/ExtraLingQA#tasks_+_datasets) |
[**Baselines**](https://github.com/mikejqzhang/ExtraLingQA#baselines) |
[**Evaluations**](https://github.com/mikejqzhang/ExtraLingQA#evaluations) |
[**Data Collection**](https://github.com/mikejqzhang/ExtraLingQA#data-collection) |
[**Citations**](https://github.com/mikejqzhang/ExtraLingQA#citations) |
[**Contact**](https://github.com/mikejqzhang/ExtraLingQA#contact) |
[**Website**](https://situatedqa.github.io/) |
[**Paper**](https://arxiv.org/abs/2109.06157)

## Introduction
This is the repository for our paper [SituatedQA: Incorporating Extra-Linguistic Contexts into QA](https://arxiv.org/abs/2109.06157). We create a task and dataset of information-seeking questions where the answers depend on the geographical or temporal context. 

## Tasks + Datasets
In our paper, we consider the following tasks which we describe in detail below: [Context-Dependent Question Identification](context-dependent_question_identification), [Temporal SituatedQA](temporal_situatedqa), [Geographical SituatedQA](geographical_situatedqa), and [Temporal Adaptation for QA](temporal_adaptation_for_qa). 

### Context-Dependent Question Identification
Context-Dependent Question Identification is the binary classification task of determining whether the answer to a given question does or does not depend on the extra-linguistic contexts. We split data based on context type, temporal (`temp`) and geographical `geo`, and training split, following the splits from each source dataset. Data for this task is stored in [/datasets/id_data](/datasets/id_data) and the format is described below:

Each example is a json with the following fields:
- `question` The input question.
- `example_id` The example id from the original dataset the question was sourced from. For WebQuestions, which does not have its own example id's, we number each example in the order the original dataset is given.
- `source_dataset` The dataset that the example was originally sourced from. The value is one of `nq.table`, `nq.passage`, `webq`, `tydi`, or `marco`.
  - Note that we split NQ-Open based on whether any of the annotators selected an answer span that within a table in the reference article.
- `label` The boolian `true` / `false` value determining whether or not the question's answer depends on its extra-linguistic context.


### Temporal SituatedQA
The Temporal SituatedQA Task involves providing the appropriate answer for a given question-plus-timestamp pair. Timestamps can be a full date (i.e., Day + Month + Year) or just the year. Data for this task is stored in [/datasets/temp_qa_data](/datasets/temp_qa_data) in the follwing format:

Each example is a json with the following fields
- `question` The input question (without context).
- `edited_question` The query-modified input question (with context).
- `example_id` The example id from the NaturalQuestions.
- `answer` List of gold answers.
- `any_answer` List of gold answers from the union of all annotated contexts of the input question.
- `date` The temporal context given as either a year (e.g., "2014") or a full date (e.g., "December 13, 1999").
- `date_type` Sampling method of the temporal context. Our sampling strategies are described in the paperi. Possible values are described below
  - `orig` _static:_ This is a temporally-independent question and the context is sampled after NaturalQuestion's collection.
  - `sampled_year` _sampled:_ The context is a year sampled between an answer's start and end dates.
  - `sampled_date` _sampled:_ The context is a full date sampled between an answer's start and end dates.
  - `start` _start_: The context is the answer's start date or year.


### Geographical SituatedQA
The Geographical SituatedQA Task involves providing the appropriate answer for a given question-plus-location pair. Data for this task is stored in [/datasets/geo_qa_data](/datasets/geo_qa_data) in the follwing format:

Each example is a json with the following fields
- `question` The input question (without context).
- `edited_question` The query-modified input question (with context).
- `example_id` The example id from the NaturalQuestions.
- `answer` List of gold answers.
- `any_answer` List of gold answers from the union of all annotated contexts of the input question.
- `location` The geographical context (e.g., "Austin, Texas").


### Temporal Adaptation for QA
In our paper, we experiment with splitting questoins based on whether the current answer has been updated since NaturalQuestoins was collected. We provide the splits we used in `/datasets/temp_splits/{PRE/POST}_{YEAR}.{SPLIT}.jsonl` where `PRE` contains questoins that have not been updated since `YEAR` and `POST` contains questoins that have been updated in or after `YEAR`.

Each example is a json with the following fields
- `question` The input question (without context).
- `example_id` The example id from the NaturalQuestions.
- `answer` List of gold answers.

In addition to supplying the spits we used in our work, we also provide the script for splitting on any year in [/datasets/get_temp_split.py](/datasets/get_temp_split.py). Example usage is as follows:
```
python /datasets/get_temp_split.py --year YEAR_TO_SPLIT_ON
```


## Datasets
### Context-Dependent Question Identification
Data for this task is stored in [/datasets/id_data](/datasets/id_data). We split data based on context type, temporal (`temp`) and geographical `geo`, and training split, following the splits from each source dataset.

Each example is a json with the following fields:
- `question`: The input question. We do not perform any post-processing after sourcing the question from the original dataset. Therefore, some may be some inconsistancies with casing or punctuation.
- `example_id`: The example id from the original dataset the question was sourced from. For WebQuestions, which does not have its own example id's, we number each example in the order the original dataset is given.
- `source_dataset`: The dataset that the example was originally sourced from. We split NQ-open based on whether any of the annotators selected an answer span that was in a table in the reference article (`table`) or not (`passage`).
  - The value is one of: `nq.table`, `nq.passage`, `webq`, `tydi`, or `marco`
- `label`: The boolian `true` / `false` value determining whether or not the question's answer depends on its extra-linguistic context.


### Context-Dependent Question Answering
Data for this task is stored in [/datasets/qa_data](/datasets/qa_data). We split data based on context type, temporal (`temp`) and geographical (`geo`), and by training, validation, and test sets. We follow the splits in the original datasets we source questions from.


## Baselines
### Context-Dependent Question Identification
Our BERT baselines can be found in `id_baselines`.

### SituatedQA Retrieval-Based Baselines (DPR)
Please refer to the official [DPR repository](https://github.com/facebookresearch/DPR) for instructions for training and evaluation as well as their pretrained checkpoints. For our experiments, we use the Wikipedia dump from Februrary 20, 2021 which is availible for download [here](https://archive.org/download/enwiki-20210220). Please refer to the ORQA repository for [instructions](https://github.com/google-research/language/tree/master/language/orqa#preprocessing-wikipedia) on preprocessing raw wikipedia. We also have the preprocessed, chunked version of the corpus availible upon request.

### SituatedQA Closed-Book Baselines (BART)
We use [@shmsw25](https://github.com/shmsw25)'s implementation and pretrained models BART trained on NQ-Open provided [here](https://github.com/shmsw25/bart-closed-book-qa). We follow their instructions for both training and inference.


## Evaluations & Leaderboard Submissions
We provide a script for getting fine-grained evaluations. For Geographically-SituatedQA, this evaluation script provides exact-match accuracy on splits of `rare` and `common` locations. For Temporally-SituatedQA, this evaluation script provides exact-match accuracy on splits of date sampling strategies: `static`, `sampled`, and `start` date types. We also provide performance on answers from the union of all contexts (`any`).

Our evaluation script takes model predicitons file to be of the same format as the Temporal and Geotraphical SituatedQA datasets, where each example has the additional `pred_answer` field containing the predicted answer string.

```
python eval/temp_eval.py PATH_TO_PREDICTIONS

python eval/geo_eval.py PATH_TO_PREDICTIONS
```

To submit to our leaderboards, please [contact](https://github.com/mikejqzhang/ExtraLingQA#contact) us by sending an email with your test set predictions given in the same format as taken by our evaluation scripts:

## Data Collection
We provide our data collection interface [/mturk/html](/mturk/html). Note that these are unpopulated templates which must be populated with input data. Both geographical and temporal `context_answer_collection` and `validation` tasks also require Google search API keys (details on Google custom search here).

## Citations
If you find our work helpful, please cite us as

```
@article{ zhang2021situatedqa,
  title={ {S}ituated{QA}: Incorporating Extra-Linguistic Contexts into {QA} },
  author={ Zhang, Michael J.Q. and Choi, Eunsol },
  journal={ Proceedings of the Conference on Empirical Methods in Natural Language Processing (EMNLP) },
  year={ 2021 }
}
```

Please also credit the creators of the datasets we built ours off of: NaturalQuestions, WebQuestions, TyDi-QA, and MS MARCO.

```
@article{ kwiatkowski2019natural,
  title={ Natural questions: a benchmark for question answering research},
  author={ Kwiatkowski, Tom and Palomaki, Jennimaria and Redfield, Olivia and Collins, Michael and Parikh, Ankur and Alberti, Chris and Epstein, Danielle and Polosukhin, Illia and Devlin, Jacob and Lee, Kenton and others },
  journal={ Transactions of the Association for Computational Linguistics (TACL) },
  year={ 2019 }
}

@article{ clark-etal-2020-tydi,
    title="{T}y{D}i {QA}: A Benchmark for Information-Seeking Question Answering in Typologically Diverse Languages",
    author={ Clark, Jonathan H. and Choi, Eunsol and Collins, Michael and Garrette, Dan and Kwiatkowski, Tom and Nikolaev, Vitaly and Palomaki, Jennimaria },
    journal={ Transactions of the Association for Computational Linguistics (TACL) },
    year={ 2020 },
}

@inproceedings{ Berant2013SemanticPO,
  title={ Semantic Parsing on Freebase from Question-Answer Pairs },
  author={ Jonathan Berant and Andrew K. Chou and Roy Frostig and Percy Liang },
  booktitle={ Proceedings of the Conference on Empirical Methods in Natural Language Processing (EMNLP) },
  year={ 2013 }
}

@article{ Campos2016MSMA,
  title={ MS MARCO: A Human Generated MAchine Reading COmprehension Dataset },
  author={ Daniel Fernando Campos and Tri Nguyen and M. Rosenberg and Xia Song and Jianfeng Gao and Saurabh Tiwary and Rangan Majumder and L. Deng and Bhaskar Mitra },
  journal={ ArXiv },
  year={ 2016 },
  volume={ abs/1611.09268 }
}
```

## Contact
Please email [Michael J.Q. Zhang](https://www.cs.utexas.edu/~mjqzhang/) at `mjqzhang [at] cs.utexas.edu` with any suggestions or questions.
