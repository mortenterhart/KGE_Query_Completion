import pandas as pd
import torch
from pykeen.predict import predict_triples
from pykeen.models import DistMult
from pykeen.triples import TriplesFactory


def main():
    model_name = 'distmult'

    print(f'[X] Loading {model_name} model')
    train_factory = TriplesFactory.from_path_binary(f'embeddings/{model_name}/training_factory')

    model = DistMult(triples_factory=train_factory)
    model.load_state_dict(torch.load(f'embeddings/{model_name}/trained_model_state_dict.pt'))
    model.eval()

    print(f'[X] Loading Wikidata5M datasets')
    wikidata5m_train = pd.read_csv('dataset/wikidata5m/wikidata5m_transductive_train.txt', sep='\t', names=['S', 'P', 'O'])
    wikidata5m_valid = pd.read_csv('dataset/wikidata5m/wikidata5m_transductive_valid.txt', sep='\t', names=['S', 'P', 'O'])
    wikidata5m_test = pd.read_csv('dataset/wikidata5m/wikidata5m_transductive_test.txt', sep='\t', names=['S', 'P', 'O'])
    wikidata5m_all = pd.concat([wikidata5m_train, wikidata5m_valid, wikidata5m_test]).values

    print('[X] Start computing predictions for all triples')

    pack = predict_triples(model=model, triples=wikidata5m_all)
    scores_df = pack.process(factory=train_factory).df

    print(f'[X] Saving predicted scores')
    scores_df.to_csv(f'embeddings/{model_name}/predicted_scores.csv')


if __name__ == '__main__':
    main()
