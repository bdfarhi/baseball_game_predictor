import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score

#reading csv and getting rid of nan values
games =pd.read_csv('games.csv', index_col=0)
games = games[games['tm'] != 'Tm']
games.drop(columns=['unnamed: 2',  "attendance", "cli", "inn",'orig. scheduled'], inplace= True)

#standardizing dataframe
games['date'] = pd.to_datetime(games['date']+ ' 2024', format='%A, %b %d %Y', errors='coerce')
games.rename(columns = {'unnamed: 4': 'venue'}, inplace=True)
games['venue'].fillna('h', inplace=True)
games['w/l'].replace('L-wo','L', inplace=True)
games['w/l'].replace('W-wo','W', inplace=True)
games.dropna(inplace= True)
games['opp_code'] = games['opp'].astype('category').cat.codes
games['hour_played'] = games['time'].str.replace(':.+', '', regex=True).astype('int')
games['d/n_code'] = games['d/n'].astype('category').cat.codes
games['venue_code'] = games['venue'].astype('category').cat.codes
games['target'] = (games['w/l'] == 'W').astype('int')
games[['wins', 'losses']] = games['w-l'].str.split('-', expand=True)
convert_dict = {'r': int, 'ra': int, 'wins': int, 'losses': int}
games = games.astype(convert_dict)
games['win_percent'] = games['wins'] / (games['wins'] + games['losses'])


#traning model

rf = RandomForestClassifier(n_estimators=50,min_samples_split=24, random_state=1)
train = games[games['date'] < '2024-06-20']
test = games[games['date'] >= '2024-06-20']
predictors = ['venue_code', 'opp_code', 'd/n_code', 'win_percent', 'wins', 'losses']
rf.fit(train[predictors], train['target'])

prediction = rf.predict(test[predictors])
#while train has columns that say if win or lose it only uses the predictors, which is all info known ahead of time 

# making model more accuracy

acc = accuracy_score(test['target'], prediction)
combined = pd.DataFrame(dict(actual=test['target'], prediction = prediction))
precision = precision_score(test['target'], prediction)
#print(precision)
#when predicted a win the team won 52.79% of the time


#imporving precision

grouped_games = games.groupby('tm')
group = grouped_games.get_group('ARI')

#having model take past wins and data into account
def rolling_average(group, cols, new_cols):
    group= group.sort_values('date')
    rolling_stats = group[cols].rolling(15, closed='left').mean()
    #takes from last 15 games
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group
cols=['r','ra','wins']
new_cols = [f"{c}_rolling" for c in cols]
games_rolling = games.groupby('tm').apply(lambda x: rolling_average(x, cols, new_cols))
games_rolling = games_rolling.droplevel('tm')
games_rolling.index = range(games_rolling.shape[0])

#continuing to make predictions

def make_predictions(data, predictors):
    train = data[data['date'] < '2024-06-20']
    test = data[data['date'] >= '2024-06-20']
    rf.fit(train[predictors], train['target'])
    prediction = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test['target'], prediction=prediction))
    precision = precision_score(test['target'], prediction)
    return combined, precision

combined, precision = make_predictions(games_rolling, predictors + new_cols)
print(precision)
#62.7% of teams model says are going to win, win

combined = combined.merge(games_rolling[['date', 'tm', 'opp', 'w/l']], left_index=True, right_index=True)
#will merge rows with same index in games and games_rolling
#print(combined)

#combining rows that represent the same games
merged=combined.merge(combined, left_on =['date', 'tm'], right_on =['date', 'opp'])
#some predictions dont match up
print('final precision is:')
print(merged[(merged['prediction_x'] == 1) & (merged['prediction_y']==0)]['actual_x'].value_counts())
print('row 1 actual / total predictions')
#actual result when model predicted team 1 to win and team 2 to lose
#was 56.5% precision in this case

