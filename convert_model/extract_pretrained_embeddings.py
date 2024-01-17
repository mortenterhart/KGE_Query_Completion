import pickle
from pathlib import Path
from typing import Literal

import numpy as np
from pykeen.triples import TriplesFactory

ModelName = Literal['complex', 'distmult', 'simple', 'transe']


def main():
    model_name: ModelName = 'complex'

    model_path = f'../pretrained_embeddings/{model_name}_wikidata5m.pkl'

    print(f'\n==== Converting pretrained {model_name} model ====\n')
    print(f'[X] Loading pretrained model {model_name} from {model_path}')

    with open(model_path, 'rb') as f:
        pretrained_model = pickle.load(f)

    print(f'[X] Loading {model_name} entity and relation mappings into triples factory')
    train_factory = TriplesFactory.from_path(
        path='dataset/wikidata5m/wikidata5m_transductive_train.txt',
        entity_to_id=pretrained_model.graph.entity2id,
        relation_to_id=pretrained_model.graph.relation2id
    )

    save_dir = Path(f'embeddings/{model_name}')
    save_dir.mkdir(exist_ok=True)

    triples_factory_path = save_dir / 'training_factory'
    entity_embeddings_path = save_dir / 'entity_embeddings.npy'
    relation_embeddings_path = save_dir / 'relation_embeddings.npy'

    print(f'[X] Saving triples factory to {triples_factory_path}')
    train_factory.to_path_binary(triples_factory_path)

    print(f'[X] Saving entity and relation embeddings to {entity_embeddings_path} and {relation_embeddings_path}')
    np.save(entity_embeddings_path, pretrained_model.solver.entity_embeddings)
    np.save(relation_embeddings_path, pretrained_model.solver.relation_embeddings)


if __name__ == '__main__':
    main()
