import datetime
import dateutil

from tqdm import tqdm
from random import randrange, uniform
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

# Time range and reporting interval
time_offset = 4  # Start simulating n days ago
simulation_buffer = time_offset * 86400

# Simulation
simulated_day = [0] * simulation_buffer


def main():
    """
    Run the task.
    """
    database_write()


def generateWaterConsumption():
    """
    Generate a water consumption pattern.
    """ 
    for day in range(time_offset):

        toilet_flushed = 0

        for hour in range(1,25):

            # between 05:00 and 07:00 run a 5 to 8 minute shower at 8 to 13 litres per minute
            if hour == 5:

                shower_start = randrange(5,8,1)
                shower_duration = randrange(300,540,1)
                shower_pressure = uniform(0.0266,0.0259)

                simulation(day, shower_start, shower_duration, shower_pressure)
            
            # flush a toilet 4 to 7 times from 05:00 till 00:00 - 5 to 12 Litres per flush
            if hour > 5 and hour < 23:

                toilet_start = randrange(5,23,1)
                toilet_flushes = randrange(4,8,1)

                if toilet_flushed < toilet_flushes:

                    flush_pressure = uniform(0.0833,0.2166)
                    toilet_duration = 60
                    toilet_flushed += 1

                    simulation(day, toilet_start, toilet_duration, flush_pressure)
                
                else:
                    continue

            # between 08:00 and 17:00 water the garden between 2 - 4 hours at average flow
            if hour == 8 and (day % 2) != 0:
                garden_start = randrange(8,13,1)
                garden_duraton = randrange(7200,14000,1)
                garden_pressure = uniform(0.1666,0.2666)

                simulation(day, garden_start, garden_duraton, garden_pressure)

            # between 08:00 and 10:00 run a washing machine - 50L a cycle
            if hour == 9:
                washing_start = randrange(8,11,1)
                washing_duration = 3600
                washing_pressure = 0.0139

                simulation(day, washing_start, washing_duration, washing_pressure)

            # between 10:00 and 13:00 create a meal 10 - 25L
            if hour == 10:
                meal_start = randrange(10,14,1)
                meal_pressure = uniform(0.013,0.015)
                meal_duration = 1100

                simulation(day, meal_start, meal_duration, meal_pressure)

            # between 14:00 and 16:00 run a washing machine - 50L a cycle
            if hour == 14:
                washing_time = randrange(14,17,1)
                washing_duration = 3600
                washing_pressure = 0.0139
                
                simulation(day, washing_time, washing_duration, washing_pressure)

            # between 18:00 and 20:00 make a small meal 2 - 10L
            if hour == 18:

                meal_start = randrange(18,21,1)
                meal_duration = 600
                meal_pressure = uniform(0.0133,0.0155)

                simulation(day, meal_start, meal_duration, meal_pressure)

            # between 20:00 and 00:00 run two 5 to 8 minute showers - 8 to 13 Litres per minute
            if hour == 20:
                
                showers = randrange(1,3,1)
                for shower in range(showers):
                    shower_start = randrange(20,23,1)
                    shower_duration = randrange(300,540,1)
                    shower_pressure = uniform(0.0266,0.0259)

                    simulation(day, shower_start, shower_duration, shower_pressure)
    


def simulation(action_day, action_start, action_duration, action_pressure):
    """
    Feed the simulation new data.
    action_day - as integers representing the current day of the simulation
    action start - as integers between 0..24 representing hte hour of the simulation
    action_duration - as whole integers representing seconds
    action pressure - as floats representing litres per second
    """
    for action in range(action_duration):

        if simulated_day[(((action_start * 60) * 60) + (86400 * action_day)) + action] > 0:
            old_value = simulated_day[(((action_start * 60) * 60) + (86400 * action_day)) + action] 
            simulated_day.insert(((((action_start * 60) * 60) + (86400 * action_day)) + action), (old_value + action_pressure))
        else:
            simulated_day.insert(((((action_start * 60) * 60) + (86400 * action_day)) + action), action_pressure)


def database_write():
    """
    Write the simulation to the database
    """
    generateWaterConsumption()

    # set progress bar size
    pbar = tqdm(simulated_day)

    # set the time the simulation should start
    time_start = (datetime.datetime.now() - dateutil.relativedelta.relativedelta(days=(time_offset - 1), hour=0, minute=0, second=0, microsecond=0)).isoformat()

    with InfluxDBClient(url=db_server, token=f'{db_username}:{db_password}', org='Main Org.') as client:

        with client.write_api() as write_api:

            for usage in simulated_day:
                time_start = (dateutil.parser.parse(time_start) + datetime.timedelta(seconds=1)).isoformat()
                point = Point("water").tag("sensor", "flow").field("flowrate", float(usage * 60)).field("usage", float(usage)).time(time_start)
                pbar.update()
                pbar.refresh()
                write_api.write(bucket=db_bucket, record=point, batch_size=10000 ,write_precision='ms')
    
    pbar.close()

                    
if __name__ == '__main__':
    main()
