import numpy as np
import pandas as pd


def main():
    predicate_metrics = pd.read_csv('metrics/predicate_metrics.csv')

    # Only consider realistic values, evaluated on both ends
    predicate_metrics = predicate_metrics.query('Type == "realistic" and Side == "both"')

    # Filter for selected metrics to compare on
    selected_metrics = ['arithmetic_mean_rank', 'hits_at_5', 'hits_at_10']

    predicate_metrics = filter_metrics(predicate_metrics, selected_metrics)

    print(predicate_metrics.info())

    print(find_largest_metric_variances(predicate_metrics).head())
    print(find_largest_metric_variances_easy(predicate_metrics).head())


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


if __name__ == '__main__':
    main()
