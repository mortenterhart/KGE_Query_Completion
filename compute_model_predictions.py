import pandas as pd
import torch
from pykeen.predict import predict_triples
from pykeen.models import DistMult, SimplE, TransE
from pykeen.triples import TriplesFactory

# Get torch device
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def main():
    model_name = 'transe'

    # Empty CUDA cache
    torch.cuda.empty_cache()

    print(f'[X] Loading {model_name} model')
    train_factory = TriplesFactory.from_path_binary(f'embeddings/dim_512/{model_name}/training_factory')

    model = TransE(
        triples_factory=train_factory,
        embedding_dim=512
    )
    model.load_state_dict(torch.load(f'embeddings/dim_512/{model_name}/trained_model_state_dict.pt'))
    model.to(device).eval()

    print(f'[X] Loading Wikidata5M datasets')
    wikidata5m_train = pd.read_csv('dataset/wikidata5m/wikidata5m_transductive_train.txt', sep='\t', names=['S', 'P', 'O'])
    wikidata5m_valid = pd.read_csv('dataset/wikidata5m/wikidata5m_transductive_valid.txt', sep='\t', names=['S', 'P', 'O'])
    wikidata5m_test = pd.read_csv('dataset/wikidata5m/wikidata5m_transductive_test.txt', sep='\t', names=['S', 'P', 'O'])
    wikidata5m_all = pd.concat([wikidata5m_train, wikidata5m_valid, wikidata5m_test]).values

    print('[X] Start computing predictions for all triples')

    mapped_triples = train_factory.map_triples(wikidata5m_all)
    mapped_triples.to(device)

    pack = predict_triples(model=model, triples=mapped_triples)
    scores_df = pack.process(factory=train_factory).df

    print(f'[X] Saving predicted scores')
    scores_df.to_csv(f'embeddings/dim_512/{model_name}/predicted_scores.csv', index=False)


if __name__ == '__main__':
    main()
