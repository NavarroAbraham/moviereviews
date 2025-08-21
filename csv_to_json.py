import pandas as pd
df = pd.read_csv('movies_initial.csv')
df.to_json('movies.json', orient='records')