import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main():
    complex_results = load_embedding_results('embeddings/ComplEx/results.json')
    distmult_results = load_embedding_results('embeddings/DistMult/results.json')
    simple_results = load_embedding_results('embeddings/SimplE/results.json')
    transe_results = load_embedding_results('embeddings/TransE/results.json')

    losses = pd.DataFrame({
        'complex': complex_results['losses'],
        'distmult': distmult_results['losses'],
        'simple': simple_results['losses'],
        'transe': transe_results['losses']
    })
    plot_losses(losses)

    metrics = pd.concat([
        pd.json_normalize(complex_results['metrics']['both']['optimistic']),
        pd.json_normalize(distmult_results['metrics']['both']['optimistic']),
        pd.json_normalize(simple_results['metrics']['both']['optimistic']),
        pd.json_normalize(transe_results['metrics']['both']['optimistic'])
    ])
    plot_metrics(metrics['hits_at_1'], ['ComplEx', 'DistMult', 'SimplE', 'TransE'], 'hits_at_1')
    plot_metrics(metrics['hits_at_3'], ['ComplEx', 'DistMult', 'SimplE', 'TransE'], 'hits_at_3')
    plot_metrics(metrics['hits_at_5'], ['ComplEx', 'DistMult', 'SimplE', 'TransE'], 'hits_at_5')
    plot_metrics(metrics['hits_at_10'], ['ComplEx', 'DistMult', 'SimplE', 'TransE'], 'hits_at_10')
    plot_metrics(metrics['arithmetic_mean_rank'], ['ComplEx', 'DistMult', 'SimplE', 'TransE'], 'arithmetic_mean_rank')
    plot_metrics(metrics['median_rank'], ['ComplEx', 'DistMult', 'SimplE', 'TransE'], 'arithmetic_mean_rank')


def load_embedding_results(file_path):
    with open(file_path) as results_file:
        return json.load(results_file)


def plot_losses(losses):
    plt.plot(losses)
    plt.legend(['Complex', 'DistMult', 'Simple', 'TransE'])
    plt.xticks(np.arange(len(losses)))
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.show()


def plot_metrics(metrics, xlabels, ylabel):
    plt.bar(np.arange(len(metrics)), metrics)
    plt.xticks(np.arange(len(metrics)), labels=xlabels)
    plt.ylabel(ylabel)
    plt.title(f'Metric {ylabel}')
    plt.show()


if __name__ == '__main__':
    main()
