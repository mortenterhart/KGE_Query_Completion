from timeit import default_timer as timer
from datetime import timedelta

from pykeen.pipeline import pipeline
from pykeen.datasets import Wikidata5M


def main():
    start = timer()

    pipeline_result = pipeline(
        dataset=Wikidata5M,
        model='TransE',
        model_kwargs={
            'embedding_dim': 32
        }
    )
    pipeline_result.save_to_directory('embeddings/dim_32/transe')

    end = timer()
    print(f'Time elapsed: {timedelta(seconds=end - start)}')


if __name__ == '__main__':
    main()
