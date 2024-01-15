import os
from timeit import default_timer as timer
from datetime import timedelta

import numpy as np
import pandas as pd
import torch
from pykeen.evaluation import RankBasedEvaluator, RankBasedMetricResults
from pykeen.triples import TriplesFactory
from pykeen.datasets import get_dataset
from pykeen.evaluation.rank_based_evaluator import _iter_ranks


def main():
    wikidata5m_test_set = pd.read_csv('dataset/knowledge_graph/wikidata5m_transductive_test.txt', sep="\t",
                                      names=['S', 'P', 'O'], header=None)
    trained_models = get_trained_models()
    print(
        f'[X] Loaded {len(trained_models)} trained models and {get_number_of_predicates(wikidata5m_test_set)} test '
        f'splits per predicate')

    wikidata5m_dataset = get_dataset(dataset='Wikidata5M')

    print(
        f'[X] Loaded {wikidata5m_dataset.get_normalized_name()} dataset with {wikidata5m_dataset.training.num_triples} '
        f'training, {wikidata5m_dataset.validation.num_triples} validation and {wikidata5m_dataset.testing.num_triples} '
        'test triples')

    print(f'[X] Starting evaluation on models')
    start = timer()
    predicate_metrics = evaluate_models_per_predicate(trained_models, wikidata5m_test_set, wikidata5m_dataset)

    print(f'[X] Finished evaluation in {timedelta(seconds=timer() - start)}')

    predicate_metrics.to_csv('metrics/predicate_metrics.csv')


def get_number_of_predicates(dataset_df):
    return dataset_df['P'].nunique()


def get_test_set_per_predicate(test_set_file):
    test_set = pd.read_csv(test_set_file, sep="\t", names=['S', 'P', 'O'], header=None)
    return test_set.groupby('P')


def get_trained_models():
    return {
        'ComplEx': _load_trained_model('embeddings/ComplEx'),
        'DistMult': _load_trained_model('embeddings/DistMult'),
        'SimplE': _load_trained_model('embeddings/SimplE'),
        'TransE': _load_trained_model('embeddings/TransE')
    }


def _load_trained_model(saved_model_dir):
    return {
        'model': torch.load(os.path.join(saved_model_dir, 'trained_model.pkl')),
        'factory': TriplesFactory.from_path_binary(os.path.join(saved_model_dir, 'training_triples'))
    }


def evaluate_models_per_predicate(trained_models, wikidata5m_test_set, dataset):
    aggregated_metrics = pd.DataFrame()
    for model_name, result in trained_models.items():
        model = result['model']
        training_factory = result['factory']

        test_factory = TriplesFactory.from_labeled_triples(
            triples=wikidata5m_test_set.values,
            entity_to_id=training_factory.entity_to_id,
            relation_to_id=training_factory.relation_to_id
        )

        evaluator = RankBasedEvaluator(clear_on_finalize=False)
        evaluator.evaluate(
            model=model,
            mapped_triples=test_factory.mapped_triples,
            additional_filter_triples=[
                dataset.training.mapped_triples,
                dataset.validation.mapped_triples
            ]
        )

        ranks_df = test_factory.tensor_to_df(
            tensor=test_factory.mapped_triples,
            **{"-".join(("rank",) + key): np.concatenate(value) for key, value in evaluator.ranks.items()},
            **{"-".join(("num_candidates", key)): np.concatenate(value) for key, value in
               evaluator.num_candidates.items()},
        )

        for (relation_id, relation_label), group in ranks_df.groupby(by=['relation_id', 'relation_label']):
            relation_ranks = {}
            relation_num_candidates = {}

            for column in group.columns:
                if column.startswith('rank-'):
                    relation_ranks[tuple(column.split('-')[1:])] = [group[column].values]
                elif column.startswith('num_candidates-'):
                    relation_num_candidates[tuple(column.split('-'))[1]] = [group[column].values]

            metric_results = RankBasedMetricResults.from_ranks(
                metrics=evaluator.metrics,
                rank_and_candidates=_iter_ranks(ranks=relation_ranks, num_candidates=relation_num_candidates)
            ).to_df()

            metric_results['relation_id'] = relation_id
            metric_results['relation_label'] = relation_label
            metric_results['model'] = model_name

            aggregated_metrics = pd.concat([aggregated_metrics, metric_results], ignore_index=True)

    return aggregated_metrics


if __name__ == '__main__':
    main()
