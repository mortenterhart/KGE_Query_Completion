import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


def main():
    predicate_metrics = pd.read_csv('metrics/predicate_metrics.csv')

    distmult_512_metrics = pd.read_csv('embeddings/dim_512/distmult/predicate_metrics.csv')
    simple_512_metrics = pd.read_csv('embeddings/dim_512/simple/predicate_metrics.csv')
    transe_512_metrics = pd.read_csv('embeddings/dim_512/transe/predicate_metrics.csv')

    # metric_names = np.sort(predicate_metrics['Metric'].unique())
    metric_names = ['arithmetic_mean_rank', 'hits_at_5', 'hits_at_10']

    print(f'[X] Plotting {len(metric_names)} different metric distributions')

    for metric in metric_names:
        complex_metrics = get_predicate_metric_distribution(predicate_metrics, metric, 'complex', 'both', 'realistic')
        distmult_metrics = get_predicate_metric_distribution(predicate_metrics, metric, 'distmult', 'both', 'realistic')
        simple_metrics = get_predicate_metric_distribution(predicate_metrics, metric, 'simple', 'both', 'realistic')
        transe_metrics = get_predicate_metric_distribution(predicate_metrics, metric, 'transe', 'both', 'realistic')

        # plot_predicate_metric_distribution(metric, complex_metrics, distmult_metrics, simple_metrics, transe_metrics)
        plot_joint_metric_distributions(metric, complex_metrics, distmult_metrics, simple_metrics, transe_metrics)


def plot_predicate_metric_distribution(metric_name,
                                       complex_metrics,
                                       distmult_metrics,
                                       simple_metrics,
                                       transe_metrics):
    # Create a figure and 4 subplots
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f'{metric_name}')

    # Plot for ComplEx
    axs[0, 0].hist(complex_metrics, bins=20, color='blue', alpha=0.7)
    axs[0, 0].set_title('ComplEx')
    axs[0, 0].set_xlabel('Metric Values')
    axs[0, 0].set_ylabel('Frequency')

    # Plot for DistMult
    axs[0, 1].hist(distmult_metrics, bins=20, color='green', alpha=0.7)
    axs[0, 1].set_title('DistMult')
    axs[0, 1].set_xlabel('Metric Values')
    axs[0, 1].set_ylabel('Frequency')

    # Plot for SimplE
    axs[1, 0].hist(simple_metrics, bins=20, color='orange', alpha=0.7)
    axs[1, 0].set_title('SimplE')
    axs[1, 0].set_xlabel('Metric Values')
    axs[1, 0].set_ylabel('Frequency')

    # Plot for TransE
    axs[1, 1].hist(transe_metrics, bins=20, color='red', alpha=0.7)
    axs[1, 1].set_title('TransE')
    axs[1, 1].set_xlabel('Metric Values')
    axs[1, 1].set_ylabel('Frequency')

    # Adjust layout to prevent clipping of titles
    plt.tight_layout()

    # Show the plot
    plt.show()


def plot_joint_metric_distributions(metric_name,
                                    complex_metrics,
                                    distmult_metrics,
                                    simple_metrics,
                                    transe_metrics):
    # Combine all DataFrames into one for joint plot
    df_all = pd.concat([
        complex_metrics.rename('ComplEx'),
        distmult_metrics.rename('DistMult'),
        simple_metrics.rename('SimplE'),
        transe_metrics.rename('TransE')
    ], axis=1)

    # Create a joint plot
    sns.set(style="whitegrid")
    sns.histplot(data=df_all, bins=20, kde=True, multiple="stack", palette="muted")

    # Add titles and labels
    plt.title(f'{metric_name} for 32-dim embeddings')
    plt.xlabel('Metric Values')
    plt.ylabel('Frequency')

    # Show the plot
    plt.show()


def get_predicate_metric_distribution(metrics: pd.DataFrame,
                                      metric_name: str,
                                      model_name: str,
                                      target: str,
                                      metric_type: str):
    return metrics.query('Metric == @metric_name and '
                         'Type == @metric_type and '
                         'model == @model_name and '
                         'Side == @target')['Value']


if __name__ == '__main__':
    main()
