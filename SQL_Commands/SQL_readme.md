SQL:
Tables - Stores the data in rows and columns
primary key - where it creates a unique identifier for each record
constraints - Rules applied to ensure the data is valid or not
  
### There are a few command categories that sql follows when we use them
  
# DDL - Data definition language
- where it deals with how we structure the data
the common cmds are
    - create - helps to create databases and its objects
    - Drop - helps to delete objects from the database
    - Alter - helps to alter the db structure
    - Truncate - helps to remove everything
# DQL - Data query language
- where it helps to retrieve/fetch the data
    - Select - helps to retrieve the data from the database
    - From - helps to retrieve from which table
    - where - helps to filter the rows before grouping
    - Group by - helps to group the rows that have the same values
    - Having - helps to filter the rows on basis of group by
    - Distinct - removes duplicate rows from the query result only, the table data stays unchanged
    - order by - helps to sort the result rows of a query in asc/desc
# DML - Data manipulation language
- where it helps to manipulate the data
    - insert - helps to insert the elements
    - update - helps to update the existing elements
    - delete - helps to remove the records from the db
# DCL - Data Control language
- where it deals with the access control of the data
    - GRANT - assigns privileges to a certain user
    - REVOKE - removes the privileges from the account
# TCL - Transaction control language
- where it allows us to run set of tasks into a single execution unit!
    - Begin Transaction - starts a new set of tasks
    - Commit - save the changes that happened during transactions
    - Rollback - undoes all the changes during transactions
    - savepoint - create save points within the current transaction
  
# Constraints and types i used while creating tables
    - Foreign key - connects a column of one table to the primary key of another table
    - On delete cascade - when the parent row is deleted, child rows get deleted automatically
    - Not null - the column must always have a value
    - Default - fills a value by itself when we don't pass one (like current_date)
    - Serial / Bigserial - auto generates id numbers for every new record
    - Timestamptz - stores date-time with timezone so one instant means the same worldwide
    - Index - makes filtering fast on columns we search a lot (like machine_id + timestamp)
  
# Extra commands i used in the api projects
    - Returning - gives back the row we just inserted/updated, no second select needed
    - On conflict do nothing - skips the row if it already exists, duplicate safe insert
    - On conflict do update - upsert, updates the existing row instead of throwing error
    - Limit / Offset - fetch only few rows and skip rows for pagination
    - Min / Max / Avg - aggregate functions, used in the statistics endpoint
    - Execute_values - batch insert 5000 rows in one shot for the big imports
    - Rowcount - tells whether the update/delete actually changed any row
    - Autocommit - needed for create database, postgres will not allow it inside a transaction
  
# Not used yet - next to learn
    - Joins - combining two tables in one query (so far my foreign key only linked the tables, joins query across them)
    - Group by / Having - learned in notes, not used in real code yet
    - Window functions - over, partition by, row_number - not used yet
    - Explain analyze - to see how postgres actually runs a query
  
# Table partitioning - what i learned in the cron_jobs partitioning exercise
    - Partition by range - splits one big table into smaller child tables by a value range
    - Partition key rule - the primary key must include the partition column (unix_ts) or postgres rejects it
    - Default partition - safety net child table that catches rows with no matching partition
    - Partition pruning - postgres scans only the matching child partitions, verify with explain analyze
    - Drop partition - removing old data becomes drop table (instant) instead of delete in batches
  
  
# UnixTimeStamp: 
- it is a reference 10 digit code from the creation of it more like "Since 1970-01-01 00:00:00 UTC that many seconds are completed w.r.t current seconds"
- we can calculate it while remove the current timestamp from the standard timestamp
- the current 10-digit unixtimestamp just shows that many seconds completed since 1970-01-01 00:00:00 UTC
  


### Show tables - used to show all the tables in the db

### Show Databases - used to show all the databses which are under the user

- Create Table
    - used to create new table in the database
    - we can define column names and their datatypes
  
    - create Table if not exists tablename
  
- Insert into
    - We can able to add elements using 
  
    - Insert into tablename(parameters) values(data)
  
- Drop table - removes a table from the db
  - Delete all rows and dependent objects 
  - recovery is possible only through a backup/databse recovery mechanism
  
  - Drop table if exists tablename

- Alter(Rename) - we can able to rename it without exisitng altering the data
  - Allows us to chnage the table name while preserving all the data

  - Alter Table tablename Rename to new_tablename - Allows us to rename a table
  - Usecases:-
    - Alter Table tablename Rename Column columnname to new_columnname - Allows us to rename a column
    - Alter Table tablename ADD columnname datatype - Allows us to add a new column
    - Alter Table tablename Modifying Column columnname new_datatype - Helps to modify the datatype
    - Alter Table tablename drop Column columnname

- Truncate Table - Helps us to remove all the records from the table without preserving it's structure
  - by doing this it can't be rollback once we executed the truncate table
  
  - Truncate Table table_name

- Cloning Table - Used to create a duplicate of an existing table
  - Helps to create backup copies of important data
  - Three types of Cloning simple, deep, Shallow

  - (simple Cloning):----
    - Create Table Clonetable Select * from tablename      
    - Here the tables will be created as copy and stores the data as well but constraints will not be preserved
  
  - (Shallow Cloning):----
    - Create Table Clonetable like tablename Select * from Clonetable
    - Here the tables will be copied same as the original but won't copy the data within the original table
  
  - (Deep Cloning):----
    - Create Table Clonetable like tablename Insert into Clonetable Select * from tablename
    - Here tables will be copied along with structure along with the data by preserving both the structure and records of the original table

- Temporary Table in SQL:--------
  - a spl table used to store the data temporarly during query execution
  - Stored in the system's temporary database and it will automatically deleted when the session ends
  - Local Temporary Table :- Accessible only to the session that created it
  - Global Temporary Table :- Accessible to Multiple sessions

- Auto Increment:-----
  - To automatically generate unique values for a column usually a primarykey
  - which helps to maintain data consistency across the databses which are available
  - In postgreSQL we use serial keyword which helps in auto-incrementing a column

- Sequences:-----
  - It helps us to generate unique numbers automatically and helps us to customize using start,increment,min and max and make sure it maintain the consistency and uniqueness

- Cache management:-----
  - It stores sequence values in memeory to improve performance and reduce disk acess