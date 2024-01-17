import pickle
from pathlib import Path

import numpy as np
import torch
from pykeen.models import TransE, ComplEx, DistMult, SimplE, ERModel
from pykeen.triples import TriplesFactory
from pykeen.nn.init import PretrainedInitializer
from extract_pretrained_embeddings import ModelName


def main():
    model_name: ModelName = 'complex'

    ModelClass = get_model_class(model_name)

    save_dir = Path(f'../embeddings/{model_name}')
    triples_factory_path = save_dir / 'training_factory'
    entity_embeddings_path = save_dir / 'entity_embeddings.npy'
    relation_embeddings_path = save_dir / 'relation_embeddings.npy'
    trained_model_path = save_dir / 'trained_model_state_dict.pt'

    print(f'[X] Loading train triples factory for {model_name} from {triples_factory_path}')
    train_factory = TriplesFactory.from_path_binary(triples_factory_path)

    print(f'[X] Loading entity and relation embeddings from {entity_embeddings_path} and {relation_embeddings_path}')
    entity_embeddings = torch.from_numpy(np.load(entity_embeddings_path))
    relation_embeddings = torch.from_numpy(np.load(relation_embeddings_path))

    print(f'[X] Creating PyKEEN model from trained {model_name} embeddings')
    model = ModelClass(
        triples_factory=train_factory,
        embedding_dim=512,
        entity_initializer=PretrainedInitializer(tensor=entity_embeddings),
        relation_initializer=PretrainedInitializer(tensor=relation_embeddings)
    )

    print(f'[X] Saving PyKEEN model to {trained_model_path}')
    torch.save(model.state_dict(), trained_model_path, pickle_protocol=pickle.HIGHEST_PROTOCOL)


def get_model_class(model_name: ModelName) -> ERModel:
    match model_name:
        case 'complex':
            return ComplEx
        case 'distmult':
            return DistMult
        case 'simple':
            return SimplE
        case 'transe':
            return TransE


if __name__ == '__main__':
    main()
