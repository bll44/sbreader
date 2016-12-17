import sys
import urllib2
import requests
from bs4 import BeautifulSoup
import os
from lib import game

session = requests.Session()
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

def login():
    login_data = {'ctl00$MainContent$ctlLogin$_UserName': 'cents109',
                  'ctl00$MainContent$ctlLogin$_Password': 'BLATCH92',
                  'ctl00$MainContent$ctlLogin$BtnSubmit': 'Login'}
    page = session.get('http://everysport247.com/default.aspx').content
    soup = BeautifulSoup(page, "html.parser")
    login_data['__VIEWSTATE'] = soup.select_one('#__VIEWSTATE')['value']
    login_data['__VIEWSTATEGENERATOR'] = soup.select_one('#__VIEWSTATEGENERATOR')['value']
    login_data['__EVENTVALIDATION'] = soup.select_one('#__EVENTVALIDATION')['value']

    session.post('http://everysport247.com/default.aspx', login_data)

    get_nfl_lines()


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
            for s in row.contents[4].strings:
                g.ats_line.append(s)
            for s in row.contents[5].strings:
                g.ou_line.append(s)
            for s in row.contents[6].strings:
                g.moneyline.append(s)

            reset += 1
            if reset > 2:
                games.append(g)
                g = game.Game()
                reset = 1
        except Exception:
            pass

    for g in games:
        print vars(g)
    # for row in rows_filtered:
    #     # get game date
    #     game_date = row.contents[1].string
    #     # cell with team name (3)
    #     td = row.contents[3]
    #     for string in td.strings:
    #         team = string
    #
    # print len(rows_filtered)


if __name__ == '__main__':
    login()
