import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
try:
    import lxml
except ImportError:
    import pip
    pip.main(['install','lxml'])
try:
    import html5lib
except ImportError:
    import pip
    pip.main(['install', 'html5lib'])

all_games =[]
standings_url = 'https://www.baseball-reference.com/leagues/majors/2024.shtml'
data = requests.get(standings_url)
if data.status_code == 200:
    print("Successfully fetched the webpage")
else:
    print(f"Failed to fetch the webpage. Status code: {data.status_code}")
    print(int(data.headers.get('Retry-After')))
soup = BeautifulSoup(data.text)
standings_table = soup.select('table.sortable')[0]
links = standings_table.find_all('a')
    # gets all anchor tabs in table
links = [l.get('href') for l in links]
    # gets href for every anchor tag
links = [l for l in links if '/teams/' in l]
    # gets anchors that are teams
team_urls = [f"https://baseball-reference.com{l}" for l in links]
for team_url in team_urls:
    team_name = team_url.split('/')[-2]
    team_game_url = f"https://www.baseball-reference.com/teams/{team_name}/2024-schedule-scores.shtml"
    data = requests.get(team_game_url)
    games = pd.read_html(data.text, match="Team Game-by-Game Schedule")[0]
    games.drop(columns=['Win', "Loss", "Save"], inplace=True)
    all_games.append(games)
    time.sleep(1)

all_games = pd.concat(all_games)
all_games.columns = [c.lower() for c in all_games.columns]
all_games.to_csv("games.csv")




