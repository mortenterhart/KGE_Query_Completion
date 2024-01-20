from typing import Literal

import pandas as pd
import torch
from pykeen.predict import predict_target
from pykeen.triples import TriplesFactory

SubsetType = Literal['train', 'valid', 'test']


def main():
    wikidata5m_train = load_wikidata5m_dataset('train')
    wikidata5m_valid = load_wikidata5m_dataset('valid')
    wikidata5m_test = load_wikidata5m_dataset('test')

    model = torch.load('embeddings/dim_32/complex/trained_model.pkl')
    model_factory = TriplesFactory.from_path_binary('embeddings/dim_32/complex/training_triples')
    print('Training set stats:')
    print(f'  Num Triples:   {model_factory.num_triples}')
    print(f'  Num Entities:  {model_factory.num_entities}')
    print(f'  Num Relations: {model_factory.num_relations} (Real: {model_factory.real_num_relations})')

    predicate_metrics = pd.read_csv('metrics/predicate_metrics.csv')

    preds = predict_tail(model, 'Q1236794', 'P31', model_factory)
    preds_df = preds.add_membership_columns(training=wikidata5m_train, validation=wikidata5m_valid, testing=wikidata5m_test).df

    print(preds_df.info())
    print('In validation set:')
    print(preds_df[preds_df['in_validation'] == True])
    print('In test set:')
    print(preds_df[preds_df['in_testing'] == True])

    predicate_label = wikidata5m_test['P'].iloc[10]
    arithmetic_mean_rank = get_predicate_metric(predicate_metrics, 'arithmetic_mean_rank', predicate_label, 'complex', 'tail', 'realistic')
    hits_at_1 = get_predicate_metric(predicate_metrics, 'hits_at_1', predicate_label, 'complex', 'tail', 'realistic')
    hits_at_3 = get_predicate_metric(predicate_metrics, 'hits_at_3', predicate_label, 'complex', 'tail', 'realistic')
    hits_at_5 = get_predicate_metric(predicate_metrics, 'hits_at_5', predicate_label, 'complex', 'tail', 'realistic')
    hits_at_10 = get_predicate_metric(predicate_metrics, 'hits_at_10', predicate_label, 'complex', 'tail', 'realistic')
    print(f'Arithmetic mean rank: {arithmetic_mean_rank}')
    print(f'Hits at 1:            {hits_at_1}')
    print(f'Hits at 3:            {hits_at_3}')
    print(f'Hits at 5:            {hits_at_5}')
    print(f'Hits at 10:           {hits_at_10}')


def load_wikidata5m_dataset(subset_type: SubsetType):
    return pd.read_csv(f'dataset/wikidata5m/wikidata5m_transductive_{subset_type}.txt', sep='\t',
                       names=['S', 'P', 'O'])


def predict_tail(model, head, relation, triples_factory):
    return predict_target(
        model=model,
        head=head,
        relation=relation,
        tail=None,
        triples_factory=triples_factory
    )


def get_predicate_metric(metrics: pd.DataFrame,
                         metric_name: str,
                         predicate_label: str,
                         model_name: str,
                         target: str,
                         metric_type: str):
    # return metrics.set_index(['Metric', 'relation_label', 'model', 'Side', 'Type']).loc[(metric_name, predicate_label, model_name, target, metric_type), 'Value']
    return metrics.query('Metric == @metric_name and '
                         'Type == @metric_type and '
                         'relation_label == @predicate_label and '
                         'model == @model_name and '
                         'Side == @target')['Value'].iloc[0]


if __name__ == '__main__':
    main()
