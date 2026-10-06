# cron jobs 
- A scheduled task where an os runs automatically at a specified time interval
- we can run programs accordingly w.r.t to the requirement

we use cron jobs to automate the tasks recursively

Cron = the service that's always running in the background, checking "is it time to do something?"

Cron job = one task you told it to do at a specific time.

### This is a linux concept where we commonly use crontab

## the famous 5 field cron expression
 ```
    * * * * *
```
minutes
hours
day of month
month
day of week

this is actually an os scheduler where the os controls the schedule

but when we deal with implementation in python we usually use a long running python scheduler which will do its work and we can check logs as well

cron schedules the cmds

we can execute in three ways
- with linux server using crontab -e with that 5 field expression
- in python we usually don't run with the help of python instead we use that interpreter
- in windows we usually use task scheduler to trigger the scripts using python exe

in production use cases the cron files usually revolve around
- entry point
- error handling
- logging
- using environment variables
- database clean up
- clear exit behavior

cron jobs can be run using 
-   bash,python,perl,php and any binary scripts.

in python we usually do/assign cronjobs through schedule module where it helps us to use those built-in function so it can know when to assign/schedule a task w.r.t time (an in-process scheduler, while real cron on linux runs the scripts through crontab)

# schedule

- it's an event where we can run the task automatically in time intervals where it is more like the python being implement the cron jobs

# Apscheduler

-   A light weight advanced python in-process task scheduling where we can use cron like capabilities
- It supports mainly three triggers
    - Datetrigger -/review one-time interval execution triggers
    - IntervalTrigger - fixed time interval triggers
    - CronTrigger - complex scheduling based on cron expressions
- Two types of schedulers
    - BackgroundScheduler - runs in the background and allows the main application to continue execution ideal for long running applications
    - BlockingScheduler - Blocks the main thread until the scheduler is shut down; best for standalone scripts where the scheduler is the primary process.
    
### Create table with below columns: ID, Unix_ts
"""Create a program with two cron jobs
1. To insert data current unix timestamp into table every 1 minute.
2. To create a partition for values in the last 10 minutes and it should run every 10 mins."""


cron_jobs  ---- root directory

\logs ---- storing the log details

\config.py --- configuring the credentials so that it can access the database user details

\db.py --- import the config file for credential details of database, and gives get_connection(database=None) which connects to the default postgres db when needed (used by setup.py while creating the database)

\logging_config.py --- importing pathlib for making the actual path as parent and create log file to it. log rotation is done by RotatingFileHandler which calls doRollover() internally when the file crosses maxBytes (10 MB) so that log files can be created and segregated between old and new log files, keeping backupCount (10) old files

\scheduler.py --- this is the actual cron jobs process where it happens while importing connection from db, (schema name, table name and ten minutes gap) from config, importing logging_config, schedule module to set the automatic schedule with time intervals

    -   setting of loggers

    - insert_current_timestamp() - where it actually 
    happens the insertion of timestamp with 1 minute difference, and it calls create_partition() with that same timestamp just before inserting so the partition always exists when the timestamp is created

    - create_partition() - where it creates the partition for the timestamp passed to it (unix_ts) on the basis of 10 minutes gap, named timestamp_data_<window_start> so that IF NOT EXISTS makes re-runs idempotent

    - run_timestamp_job() - entry point of the insert_current_timestamp()

    - run_partition_job() - an entry point of the create_partition()

    - run_scheduler() - where the actual cron jobs done with the help of schedule module so that it can directly implement the cron job for every 1 minute

    - main entry point - running scheduler.py directly calls run_scheduler() so to execute all the code snippets properly!

\setup.py - setting up database with the imports from config, db for db name,schema and connection respectively

    - create_database() - create a db with autocommit while connecting to the default db

    - create_schema() - creating a schema and being verified

    - create_table() - creating a table with id and unix_ts and do partitions based on timestamp and being verified, plus a _default partition as the safety net that catches rows with no matching partition

    - initialize_database() - an entry point for those three functions

    - main() - an entry point for initialize_database


### keep built-in functions that are being used
- Primary Key is being used for look up purpose either w.r.t the id/unix_ts

- load_dotenv() - loading of db credentials with the help of dotenv import

- psycopg2.connect() - connecting to the db with the env variables from psycopg2 import

- RotatingFileHandler - a logging import where it rotates the file with the help doRollover() so that log files can be created and segregated between old and new log file w.r.t the size

- int(time.time()) - converting the float unix_timestamp from time.time() into an integer unix_timestamp

- connection.cursor() - where it helps to tell the python to start the sql command

- cursor.execute() - where we can able to execute the db commands in python scripts

- logging.getLogger() - we can pass the name of the logger that is shown in the terminal

- schedule.every(1).minute.do() - assign the automated tasks so that it will do on its own every 1 minute

- schedule.every(10).minutes.do() - assign the automated tasks so that it will do on its own every  10 minute

- schedule.run_pending() - helps to check the pending jobs

- Blockingscheduler - as these cron_jobs are one time continous runnable scripts

- scheduler.add_job(
        run_timestamp_job, - the function we wants to execute
        "cron", - which type of trigger
        minute="*/1", - fires every minute
        id="insert_timestamp", - inserting unique identifier for this job
    )


| **Features** | APScheduler | Schedule
| **Complexity** | Feature-rich, production-grade | Lightweight, simple API |
| **Triggers** | Cron, interval, date, calendar | Interval-based only |
| **Persistence** | Yes (SQL, MongoDB, Redis, SQLite) | No — jobs lost on restart |
| **Concurrency** | Thread/process/async executors | Single-threaded by default |
| **Best for** | Production apps, web frameworks, complex schedules | Quick scripts, prototypes, simple recurring tasks |