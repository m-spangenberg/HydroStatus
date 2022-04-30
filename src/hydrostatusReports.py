import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import requests

from dotenv import dotenv_values

config = dotenv_values(".env")

# Database
db_username = config["INFLUXDB_USER"]
db_password = config["INFLUXDB_USER_PASSWORD"]
db_server = config["INFLUXDB_SERVER"]
db_name = config["INFLUXDB_DB"]

# Alarms
usage_alarm = 300

# Total usage queries
realtime_total = 'SELECT sum("usage") AS realtime_usage FROM "watermeter"."retainweek"."water" WHERE time > now() - 1m'
hourly_total = 'SELECT sum("usage") AS hourly_usage FROM "watermeter"."retainweek"."water" WHERE time > now() - 1h'
daily_total = 'SELECT sum("usage") AS daily_usage FROM "watermeter"."retainweek"."water" WHERE time > now() - 1d'
weekly_total = 'SELECT sum("usage") AS weekly_usage FROM "watermeter"."retainweek"."water" WHERE time > now() - 7d'
monthly_total = 'SELECT sum("1m-usage") AS monthly_usage FROM "watermeter"."retainmonth"."minute" WHERE time > now() - 4w'

total_queries = [realtime_total, hourly_total, daily_total, weekly_total, monthly_total]

# Graph Styling

mpl.style.use("dark_background")

mpl.rcParams['font.size'] = 10
mpl.rcParams['lines.antialiased'] = True
mpl.rcParams['text.antialiased'] = True
mpl.rcParams['font.monospace'] = 'DejaVu Sans Mono'
mpl.rcParams['text.color'] = '#b0b3b8'  # light grey
mpl.rcParams['axes.labelcolor'] = '#b0b3b8'  # light grey
mpl.rcParams['xtick.color'] = '#b0b3b8'  # light grey
mpl.rcParams['ytick.color'] = '#b0b3b8'  # light grey
mpl.rcParams['figure.facecolor'] = '#353c51'  # dark blue grey
mpl.rcParams['axes.facecolor'] = '#353c51'  # dark blue grey
mpl.rcParams['savefig.facecolor'] = '#353c51'  # dark blue grey
mpl.rcParams['axes.grid'] = True
mpl.rcParams['grid.alpha'] = 0.4
mpl.rcParams['axes.axisbelow'] = True
mpl.rcParams['grid.color'] = '#506680'  # soft blue grey


def generateReports():
    """
    Generate report graphs
    """
    # Query the database
    t = generateUsage()

    with requests.Session() as s:
        
        for q in total_queries:

            cq = s.get(f'{db_server}/query?db={db_name}&u={db_username}&p={db_password}&q={q}')

            valuetoprint = cq.json()

            try:
                t.append(valuetoprint['results'][0]['series'][0]['values'][0][1])
            except KeyError:
                t.append(0)

    reportDay(s, t)
    reportWeek(s, t)
    reportMonth(s, t)


def generateUsage():
    """
    Check the current metrics on the database
    """
    # Query the database
    total_results = []

    with requests.Session() as s:
        
        for q in total_queries:

            cq = s.get(f'{db_server}/query?db={db_name}&u={db_username}&p={db_password}&q={q}')

            valuetoprint = cq.json()

            try:
                total_results.append(valuetoprint['results'][0]['series'][0]['values'][0][1])
            except KeyError:
                total_results.append(0)

    return total_results


def usageMetrics():
    """
    Format a usage report for the client
    """
    clientUsage = generateUsage()
    usageReport = f"Water Usage Totals:\nCurrent: {clientUsage[0]:.2f} L/min \nLast Hour: {clientUsage[1]:.2f} L/hour\nLast 24 Hours: {clientUsage[2]:.2f} Litres\nLast 7 Days: {clientUsage[3]:.2f} Litres\nLast 4 Weeks: {clientUsage[4]:.2f} Litres"

    return usageReport


def reportDay(s, t):
    """
    Report the hourly totals for water used over the last 24 hours
    """
    daily_range = (f'SELECT sum("usage") AS range FROM "watermeter"."retainweek"."water" WHERE time > now() - 1d GROUP BY time(1h)')

    # we need a try, except here to catch KeyErrors.
    cq = s.get(f'{db_server}/query?db={db_name}&u={db_username}&p={db_password}&q={daily_range}')
    qv = cq.json()

    df = pd.DataFrame.from_dict(qv['results'][0]['series'][0]['values'])
    df = df.fillna(0)
    df = df.rename({0: 'time', 1: 'litres'}, axis=1)
    # df = df.set_index('time') -- how to get this into hour readings? eg: 00:00 to 23:59

    df.plot(kind='bar', color='#b3c3f3', xlabel='Hours', ylabel='Litres', title=f'Water Usage Per Day | Total: {t[2]:.2f} Litres \n Reported at {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    plt.savefig(f'graphs/report-day.png')


def reportWeek(s, t):
    """
    Report the daily totals for water used over the last 7 days
    """
    weekly_range = (f'SELECT sum("usage") AS range FROM "watermeter"."retainweek"."water" WHERE time > now() - 1w GROUP BY time(1d)')

    cq = s.get(f'{db_server}/query?db={db_name}&u={db_username}&p={db_password}&q={weekly_range}')
    qv = cq.json()

    df = pd.DataFrame.from_dict(qv['results'][0]['series'][0]['values'])
    df = df.fillna(0)
    df = df.rename({0: 'time', 1: 'litres'}, axis=1)
    # df = df.set_index('time') -- how to get this into day readings? eg: Jan 1 to Jan 7

    df.plot(kind='bar', color='#b3c3f3', xlabel='Days', ylabel='Litres', title=f'Water Usage Per Week | Total: {t[3]:.2f} Litres \n Reported at {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    plt.savefig(f'graphs/report-week.png')


def reportMonth(s, t):
    """
    Report the daily totals for water used over the last 4 weeks
    """
    monthly_range = (f'SELECT sum("1m-usage") AS range FROM "watermeter"."retainmonth"."minute" WHERE time > now() - 4w GROUP BY time(1d)')

    cq = s.get(f'{db_server}/query?db={db_name}&u={db_username}&p={db_password}&q={monthly_range}')
    qv = cq.json()

    df = pd.DataFrame.from_dict(qv['results'][0]['series'][0]['values'])
    df = df.fillna(0)
    df = df.rename({0: 'time', 1: 'litres'}, axis=1)
    # df = df.set_index('time')  -- how to get this into day readings? eg: Feb 1 to Feb 28
    
    df.plot(kind='bar', color='#b3c3f3', xlabel='Days', ylabel='Litres', title=f'Water Usage Per Month | Total: {t[4]:.2f} Litres \n Reported at {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    plt.savefig(f'graphs/report-month.png')
    

def checkAlert():
    """
    checks the database for usage over the last hour, used by `monitorAlert()` in `hydrostatusBot`.
    """
    alert_range = f'SELECT sum("usage") AS range FROM "watermeter"."retainweek"."water" WHERE time > now() - 1h GROUP BY time(1h)'
    
    with requests.Session() as s:
        
        # we need a try, except here to catch KeyErrors.
        cq = s.get(f'{db_server}/query?db={db_name}&u={db_username}&p={db_password}&q={alert_range}')

        qv = cq.json()

        df = pd.DataFrame.from_dict(qv['results'][0]['series'][0]['values'])
        df = df.fillna(0)
        df = df.rename({0: 'time', 1: 'litres'}, axis=1)
        qt = df['litres'].sum()

    return qt

