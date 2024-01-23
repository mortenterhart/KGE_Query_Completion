import numpy as np
import pandas as pd
import requests
from matplotlib import pyplot as plt


def main():
    predicate_metrics = pd.read_csv('metrics/predicate_metrics.csv')

    # Only consider realistic values, evaluated on both ends
    predicate_metrics = predicate_metrics.query('Type == "realistic" and Side == "both"')

    # Filter for selected metrics to compare on
    selected_metrics = ['arithmetic_mean_rank', 'hits_at_5', 'hits_at_10']

    predicate_metrics = filter_metrics(predicate_metrics, selected_metrics)

    variances_df = find_largest_metric_variances(predicate_metrics).head(5)

    print('Selected predicates and variances:')
    print(variances_df)

    example_predicates = predicate_metrics[predicate_metrics['relation_label'].isin(variances_df['relation_label'])]

    plot_selected_predicate_metrics(example_predicates)


def filter_metrics(predicate_metrics, selected_metrics):
    return predicate_metrics[predicate_metrics['Metric'].isin(selected_metrics)]


def find_largest_metric_variances(predicate_metrics):
    predicates = predicate_metrics['relation_label'].unique()
    metric_names = predicate_metrics['Metric'].unique()
    model_names = predicate_metrics['model'].unique()

    metric_values = np.empty((len(predicates), len(metric_names), len(model_names)))

    for y, metric_name in enumerate(metric_names):
        for z, model_name in enumerate(model_names):
            metrics = predicate_metrics.query('Metric == @metric_name and model == @model_name')

            metric_values[:, y, z] = metrics['Value'].values

    metric_variances = np.var(metric_values, axis=2).mean(axis=1)

    variances_df = pd.DataFrame({
        'relation_label': predicates,
        'variance': metric_variances
    })

    return variances_df.sort_values(by='variance', ascending=False, ignore_index=True)


def find_largest_metric_variances_easy(predicate_metrics):
    predicates = predicate_metrics['relation_label'].unique()

    metric_variances = []
    for pred in predicates:
        arithmetic_mean_rank = predicate_metrics.query('relation_label == @pred and Metric == "arithmetic_mean_rank"')['Value']
        hits_at_5 = predicate_metrics.query('relation_label == @pred and Metric == "hits_at_5"')['Value']
        hits_at_10 = predicate_metrics.query('relation_label == @pred and Metric == "hits_at_10"')['Value']

        pred_variance = np.mean([
            np.var(arithmetic_mean_rank),
            np.var(hits_at_5),
            np.var(hits_at_10)
        ])

        metric_variances.append([pred, pred_variance])

    variances_df = pd.DataFrame(metric_variances, columns=['relation_label', 'variance'])

    return variances_df.sort_values(by='variance', ascending=False, ignore_index=True)


def plot_selected_predicate_metrics(predicate_metrics):
    example_predicates = predicate_metrics['relation_label'].unique()
    wikidata_labels = get_wikidata_property_names(example_predicates)

    for pred, w_label in zip(example_predicates, wikidata_labels):
        pred_df = predicate_metrics[predicate_metrics['relation_label'] == pred]

        # Sort by model name to ensure correct ordering
        pred_df = pred_df.sort_values(by='model')

        # Filter values for each metric
        amr_values = pred_df[pred_df['Metric'] == 'arithmetic_mean_rank']
        hits5_values = pred_df[pred_df['Metric'] == 'hits_at_5']
        hits10_values = pred_df[pred_df['Metric'] == 'hits_at_10']

        # Create subplots
        fig, axs = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Metrics for predicate: {pred} (Wikidata: {w_label})')

        axs[0, 0].bar(amr_values['model'], amr_values['Value'], color=['blue', 'green', 'orange', 'red'])
        axs[0, 0].set_title('Arithmetic Mean Rank')

        axs[0, 1].bar(hits5_values['model'], hits5_values['Value'], color=['blue', 'green', 'orange', 'red'])
        axs[0, 1].set_title('Hits at 5')

        axs[1, 0].bar(hits10_values['model'], hits10_values['Value'], color=['blue', 'green', 'orange', 'red'])
        axs[1, 0].set_title('Hits at 10')

        # Adjust layout to prevent clipping of titles
        plt.tight_layout()

        # Show the plot
        plt.show()


def get_wikidata_property_names(property_ids: list):
    wikidata_api = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'wbgetentities',
        'ids': '|'.join(property_ids),
        'languages': 'en',
        'props': 'labels',
        'format': 'json'
    }

    response = requests.get(wikidata_api, params).json()

    property_names = []
    for pid in property_ids:
        property_names.append(response['entities'][pid]['labels']['en']['value'])

    return property_names


if __name__ == '__main__':
    main()
