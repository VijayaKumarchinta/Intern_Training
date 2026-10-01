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