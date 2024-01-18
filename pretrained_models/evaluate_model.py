import numpy as np
import pandas as pd
import torch
from pykeen.datasets import get_dataset
from pykeen.evaluation import RankBasedEvaluator, RankBasedMetricResults
from pykeen.evaluation.rank_based_evaluator import _iter_ranks
from pykeen.models import DistMult
from pykeen.triples import TriplesFactory

from extract_pretrained_embeddings import ModelName


def main():
    model_name: ModelName = 'distmult'

    print('[X] Loading Wikidata5M test set')
    wikidata5m_test = pd.read_csv('../dataset/wikidata5m/wikidata5m_transductive_test.txt', sep='\t',
                                  names=['S', 'P', 'O'], header=None)
    wikidata5m_dataset = get_dataset(dataset='Wikidata5M')

    print(f'[X] Loading train factory for {model_name}')
    train_factory = TriplesFactory.from_path_binary(f'../embeddings/{model_name}/training_factory')

    print(f'[X] Loading {model_name} model')
    model = DistMult(
        triples_factory=train_factory,
        embedding_dim=512
    )
    model.load_state_dict(torch.load(f'../embeddings/{model_name}/trained_model_state_dict.pt'))

    print(f'[X] Starting evaluation on Wikidata5M test set with {model_name}')
    predicate_metrics = evaluate_model_per_predicate(model, model_name, train_factory, wikidata5m_test, wikidata5m_dataset)

    print(f'[X] Finished evaluation, saving results')
    predicate_metrics.to_csv(f'../embeddings/{model_name}/predicate_metrics.csv')


def evaluate_model_per_predicate(trained_model, model_name, train_factory, wikidata5m_test_set, dataset):
    test_factory = TriplesFactory.from_labeled_triples(
        triples=wikidata5m_test_set.values,
        entity_to_id=train_factory.entity_to_id,
        relation_to_id=train_factory.relation_to_id
    )

    evaluator = RankBasedEvaluator(clear_on_finalize=False)
    evaluator.evaluate(
        model=trained_model,
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

    aggregated_metrics = pd.DataFrame()

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
