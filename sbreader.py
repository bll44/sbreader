import sys
import urllib2
import requests
from bs4 import BeautifulSoup
import os
from lib import game
import mysql.connector
import uuid
from datetime import date, datetime, timedelta

# sb site credentials file
sb_site_creds = [line.rstrip('\n') for line in open(os.getcwd() + '/.login')]

session = requests.Session()
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

# connect to MySQL database
mysql_creds = [line.rstrip('\n') for line in open(os.getcwd() + '/.mysql_login')]
cnx = mysql.connector.connect(user=mysql_creds[0], password=mysql_creds[1],
                              host='127.0.0.1', database='sbreader')
def login():

    login_data = {'ctl00$MainContent$ctlLogin$_UserName': sb_site_creds[0],
                  'ctl00$MainContent$ctlLogin$_Password': sb_site_creds[1],
                  'ctl00$MainContent$ctlLogin$BtnSubmit': 'Login'}
    page = session.get('http://everysport247.com/default.aspx').content
    soup = BeautifulSoup(page, "html.parser")
    login_data['__VIEWSTATE'] = soup.select_one('#__VIEWSTATE')['value']
    login_data['__VIEWSTATEGENERATOR'] = soup.select_one('#__VIEWSTATEGENERATOR')['value']
    login_data['__EVENTVALIDATION'] = soup.select_one('#__EVENTVALIDATION')['value']

    session.post('http://everysport247.com/default.aspx', login_data)

    nfl_lines = get_nfl_lines()
    past_lines = get_past_lines()
    spreadcnc(nfl_lines, past_lines)

    for line in nfl_lines:
        insert_game(line)


def get_nfl_lines():
    nfl_event_validation = open(os.getcwd() + '/event_validations/nfl_event_validation').read()
    nfl_view_state = open(os.getcwd() + '/view_states/nfl_view_state').read()
    data = {'__EVENTTARGET': 'ctl00$WagerContent$idx_1x1',
            '__VIEWSTATE': nfl_view_state,
            '__VIEWSTATEGENERATOR': '3DB83FCB',
            '__EVENTVALIDATION': nfl_event_validation}
    page = session.post('http://everysport247.com/wager/CreateSports.aspx?WT=0', data).content
    soup = BeautifulSoup(page, 'html.parser')
    tables = soup.find_all('table')
    table = tables[1]

    trows = table.find_all('tr')

    x = 0
    games = []
    g = game.Game()
    reset = 1
    for row in trows:
        try:
            td = row.contents[3]
            if td.span['id'] != 'teamlogo':
                continue

            team_name = (td.span['class'][0] + ' ' + td.span['class'][1]).replace('football-', '')
            date = row.contents[1].string.strip()
            g.date += date + ' '
            g.teams.append(team_name)
            g.guid = row.contents[4].input['value'][2:9]
            g.ats_line.append(row.contents[4].input['value'][10:].replace('_', ' '))
            # for s in row.contents[4].strings:
            #     g.ats_line.append(s.replace(u'\xbd', '.5'))
            g.ou_line.append(row.contents[5].input['value'][10:].replace('_', ' '))
            # for s in row.contents[5].strings:
            #     g.ou_line.append(s.replace(u'\xbd', '.5'))
            g.moneyline.append(row.contents[6].input['value'][12:])
            # for s in row.contents[6].strings:
            #     g.moneyline.append(s.replace(u'\xbd', '.5'))

            reset += 1
            if reset > 2:
                games.append(g)
                g = game.Game()
                reset = 1
        except Exception:
            pass

    for g in games:
        # correct the date to add the year
        date = datetime.strptime((str(g.date)).strip(), '%b %d %I:%M %p')
        if date.month != datetime.now().month:
            year = datetime.now().year + 1
        else:
            year = datetime.now().year
        g.date = date.strftime('%Y-%m-%d %H:%M').replace('1900', str(year))

    return games
    # for g in games:
    #     insert_game(g)
    #
    # spreadcnc()
    # cnx.close()

def insert_game(game):
    cursor = cnx.cursor()

    today = datetime.now()

    add_game = ("INSERT INTO games "
                "(gameid, date, team1, team2, ou1, ou2, ats1, ats2, ml1, ml2, update_time) "
                "VALUES (%(gameid)s, %(date)s, %(team1)s, %(team2)s, %(ou1)s, %(ou2)s, %(ats1)s, %(ats2)s, %(ml1)s, %(ml2)s, %(update)s)")
    data_game = {
        'gameid': game.guid,
        'date': game.date,
        'team1': game.teams[0],
        'team2': game.teams[1],
        'ou1': game.ou_line[0],
        'ou2': game.ou_line[1],
        'ats1': game.ats_line[0],
        'ats2': game.ats_line[1],
        'ml1': game.moneyline[0],
        'ml2': game.moneyline[1],
        'update': datetime.now()
    }

    cursor.execute(add_game, data_game)
    cnx.commit()
    cursor.close()

def get_past_lines():
    cursor = cnx.cursor()

    from_date = datetime.now() - timedelta(seconds=1200)
    to_date = datetime.now()

    query_games = ("SELECT * FROM games WHERE update_time > %(from_date)s")
    cursor.execute(query_games, {'from_date': from_date})

    past_games = []
    row = cursor.fetchone()
    while row is not None:
        g = game.Game()
        data = dict(zip(cursor.column_names, row))
        g.teams.append(data['team1'])
        g.teams.append(data['team2'])
        g.guid = data['gameid']
        g.ats_line.append(data['ats1'])
        g.ats_line.append(data['ats2'])
        g.ou_line.append(data['ou1'])
        g.ou_line.append(data['ou2'])
        g.moneyline.append(data['ml1'])
        g.moneyline.append(data['ml2'])
        g.date = data['date']
        g.update_time = data['update_time']
        past_games.append(g)
        row = cursor.fetchone()

    cursor.close()

    return past_games

def spreadcnc(new_lines, past_lines):


if __name__ == '__main__':
    login()
