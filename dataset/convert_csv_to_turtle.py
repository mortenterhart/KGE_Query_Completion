import pandas as pd

wikidata_prefix = 'https://www.wikidata.org/wiki/'


def main():
    df = pd.read_csv('./wikidata5m/wikidata5m_transductive_train.txt', sep='\t', names=['S', 'P', 'O'])

    # Transform triples to Turtle format in the dataframe
    turtle_df = df.apply(row_to_turtle, axis=1)

    turtle_file = './wikidata5m/wikidata5m_transductive_train.ttl'
    with open(turtle_file, 'w') as f:
        f.write(f'@prefix wd: <{wikidata_prefix}>\n\n')

    turtle_df.to_csv(turtle_file, mode='a', header=False, index=False)


def row_to_turtle(row):
    return f'wd:{row["S"]} wd:{row["P"]} wd:{row["O"]} .'


if __name__ == '__main__':
    main()
