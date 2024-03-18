import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main():
    df = pd.read_csv('dataset/wikidata5m/wikidata5m_transductive_train.txt', sep='\t', names=['S', 'P', 'O'])
    get_predicate_frequencies(df)
    get_object_frequencies_per_predicate(df)
    get_subject_frequencies_per_predicate(df)


def get_predicate_frequencies(df):
    p_frequencies = df['P'].value_counts(sort=True)
    print(f'Predicate frequencies length: {p_frequencies.size}')
    plt.bar(np.arange(p_frequencies.size), p_frequencies)
    plt.show()


def get_object_frequencies_per_predicate(df):
    o_frequencies = df[['P', 'O']].groupby('P').nunique()['O']
    print(f'Object frequencies length: {o_frequencies.size}')
    plt.bar(np.arange(o_frequencies.size), o_frequencies)
    plt.show()


def get_subject_frequencies_per_predicate(df):
    s_frequencies = df[['S', 'P']].groupby('P').nunique()['S']
    print(f'Subject frequencies length: {s_frequencies.size}')
    plt.bar(np.arange(s_frequencies.size), s_frequencies)
    plt.show()


if __name__ == '__main__':
    main()
