import datetime
import dateutil

from tqdm import tqdm
from time import sleep
from random import randrange
from influxdb_client import InfluxDBClient, Point
from dotenv import dotenv_values

config = dotenv_values(".env")

# Database
db_server = config["INFLUXDB_SERVER"]
db_username = config["INFLUXDB_USER"]
db_password = config["INFLUXDB_USER_PASSWORD"]
db_name = config["INFLUXDB_DB"]
db_retention_policy = config["INFLUXDB_RP"]
db_bucket = f'{db_name}/{db_retention_policy}'


def main():
    """
    Run the task.
    """
    database_stream()


def usage(resolution):
    """
    50L/min theoretical max
    25L/min nominal
    20L/min average
    <8L/min low-pressure
    ~3L/min theoretical min
    """
    flow = randrange(25)
    waterusage = (flow / 60) * resolution

    return waterusage


def database_stream():
    """
    Write the simulation to the database
    """
    start_time = (datetime.datetime.utcnow() - dateutil.relativedelta.relativedelta(microsecond=0)).isoformat()
    stream_counter = 0
    stream_time = 15  # in minutes
    resolution = 1  # in seconds
    duration = int(stream_time * 60)

    with InfluxDBClient(url=db_server, token=f'{db_username}:{db_password}', org='Main Org.') as client:

        with client.write_api() as write_api:

            for moment in tqdm(range(0,duration,resolution)) :
                flow = usage(resolution)
                current_time = (datetime.datetime.utcnow() - dateutil.relativedelta.relativedelta(microsecond=0)).isoformat()
                point = Point("water").tag("sensor", "flow").field("flowrate", float(flow * 60)).field("usage", float(flow)).time(current_time)
                write_api.write(bucket=db_bucket, record=point, write_precision='ms')
                sleep(resolution)

                    
if __name__ == '__main__':
    main()