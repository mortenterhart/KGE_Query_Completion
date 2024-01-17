import pickle
from pathlib import Path

import torch
from pykeen.models import TransE, ComplEx, DistMult, SimplE
from pykeen.triples import TriplesFactory
from pykeen.nn.init import PretrainedInitializer


def main():
    pretrained_models = get_pretrained_model_paths()

    for model_name, model_props in pretrained_models.items():
        model_path = model_props['path']
        ModelClass = model_props['class']

        print(f'\n==== Converting pretrained {model_name} model ====\n')
        print(f'[X] Loading pretrained model {model_name} from {model_path}')
        with open(model_path, 'rb') as f:
            pretrained_model = pickle.load(f)

        print('Members of pretrained_model.graph:', dir(pretrained_model.graph))
        print('Members pretrained_model.solver;', dir(pretrained_model.solver))
        print('Type of pretrained_model.solver.entity_embeddings;', type(pretrained_model.solver.entity_embeddings))
        print('Type of pretrained_model.solver.relation_embeddings;', type(pretrained_model.solver.relation_embeddings))

        print(f'[X] Loading {model_name} entity and relation mappings into triples factory')
        train_factory = TriplesFactory.from_path(
            path='dataset/wikidata5m/wikidata5m_transductive_train.txt',
            entity_to_id=pretrained_model.graph.entity2id,
            relation_to_id=pretrained_model.graph.relation2id
        )

        print(f'[X] Creating PyKEEN model from trained {model_name} embeddings')
        entity_embeddings = torch.from_numpy(pretrained_model.solver.entity_embeddings)
        relation_embeddings = torch.from_numpy(pretrained_model.solver.relation_embeddings)

        model = ModelClass(
            triples_factory=train_factory,
            embedding_dim=512,
            entity_initializer=PretrainedInitializer(tensor=entity_embeddings),
            relation_initializer=PretrainedInitializer(tensor=relation_embeddings)
        )

        save_dir = Path(f'embeddings/{model_name}')
        save_dir.mkdir(exist_ok=True)

        print(f'[X] Saving converted model and mappings to {save_dir}')
        torch.save(model.state_dict(), save_dir.joinpath('trained_model_state_dict.pt'),
                   pickle_protocol=pickle.HIGHEST_PROTOCOL)
        train_factory.to_path_binary(save_dir.joinpath('training_factory'))


def get_pretrained_model_paths():
    return {
        'complex': {
            'path': 'pretrained_embeddings/complex_wikidata5m.pkl',
            'class': ComplEx
        },
        'distmult': {
            'path': 'pretrained_embeddings/distmult_wikidata5m.pkl',
            'class': DistMult
        },
        'simple': {
            'path': 'pretrained_embeddings/simple_wikidata5m.pkl',
            'class': SimplE
        },
        'transe': {
            'path': 'pretrained_embeddings/transe_wikidata5m.pkl',
            'class': TransE
        }
    }


if __name__ == '__main__':
    main()
