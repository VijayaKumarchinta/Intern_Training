# SQL

## Core features we got

### Common data types that are used in sql

- `Integer, bigint,smallint` - used for whole numbers
- `Numeric()` - used for exact decimal numbers
- `Text,varchare()` - used fir text
- `Boolean` - used for true/false types
- `date,timestamp,timestampz` - used whe we deal with date and timeand use `timestampz` for event times
- `UUID` - used for unique ID's
- `jsonb` - used for semi structured data
- `integer[],text[]` - used for list in arrays

### Constraints - let the db set the rules dealing with the data

- `primary key` - so the rows can be identified as unique and not nul
- `foreign key/references` - which refer the pk of another table
- `unique` - prevent duplicates
- `NOT NULL` - make sure you give the value
- `check` - acts like a custom rule
- `default` - when a none is give this is used

### SELECT,DISTINCT,aliases,expressions

- `to retrieve all columns` - ``select * from table_name`
- `when we want to retrieve what are needed` - `instead of * note down the required column names
- `to retrieve unique values` - add `distinct` keyword before column names while writing the select cmd
- `to get unique combinations` - add `distinct` then join the column of our liking
- `to make names for column name` - add `as` before the column name then followed by table name

`Latest orders per customers` - ``select distinct on(customer_id) cus_id,id,created _at from orders order by cus_id,created_at desc``

we normally use this when we want want api responses to select only the needed columns

### Where,comparison,logical operators

- `=,<>,<=,>=` - comparisons operators
- AND,OR,NOT - logical operators

we use these along with where clause in dashboards,admin filters and when we want to hide something

### IN,BETWEEN,LIKE,ILIKE,IS NULL

- `when we want match a list`- use `IN` after `where`
- `when we want to see the range` - use `between` after `where`
- `when we want to find out the characters that start,ends or got any` - use `like` after the `where`
- `when we want to check null values` - use `IS NULL/IS NOT NULL` after `where`

Realtime use case are

- `IN` - used in ui when we filter multiple columns
- `Between` - used for the ranges
- `ILIKE` -for search box

### Order by ,limit, offset

- `when we want to sort the columns` - use `Order by` followed by `from`
- `when we want till certain entries` - use `limit` followed by `order by`
- `when we want to allow all the data but in pages` - use `offset` followed by `limit` followed by `order by`

Realtime use case are

- `Order by` followed by `limit` used for leaderboard
- `limit` followed by `offset` allows you to store data in pages

```Data manipulation and aggregation```

### Insert, Returning

-`when we want to add data into tables` - we use `Insert into` followed by table_name() `values()`
-`when we want to return the modified data soon after inserting,deleting any crud operations` - use `returning c1,c2` at the end of the query

Realtime use case are

- in signup requests,cart checkouts

### Update

- `when we want to update the data in the tables` - use `update` followed by `where` otherwise it will update everywhere

Realtime use case are

- order lifecycle
- while doing profile edits

### Delete and Truncate

- `when we want to delete particular data from the tables` - use `delete`
- `when we want to remove all rows` - use `truncate`

Realtime use case are

- most them use a soft delete so retrieving become easy when we delete it

### Aggregate functions we use alias to make it easy

- `when we want to count the data` - we use `count(*)` followed by `select`
- `when we want to extract particular column/unique data` - we use `count(distinct col_name)` followed by `select`
- `when we want to find out total or mean` - use `sum()/avg()`
- `when we want to find the minimum and maximum values` - use `min()/max()`

Realtime use case are

- we use them in kpi cards,to check the quality

### Group by and having

- `when we want to bundle rows with same value` - use `group by`
- `when we want to filter the groups after aggregation` - use `having`

Realtime use case are

- to generate reports,segmentation and to check frauds

### Joins and relational thinking

- `when we want only the matching rows in both tables` - use `inner join`
- `when we want to match all rows from left table + matching rows from right` - use `left join`
- `when we want to match all rows from right table + matching rows from left` - use `right join`
- `when we want to match all rows from both` - use `full join`
- `when we want to match with every combination` - use `cross join`
- `when we a table want to joined itself` - use self join
Realtime use cases are

- `inner join/join` - when we see the data who are matching from the both tables
- `left join/right join` - when we want to see the data even though they got nothing
- `full join` - used when we are comparing tables

### Relation's and bridges between tables

- `one-one` - fk's with unique or shared pk's(use with their user's profile)
- `one-many` - fk's but on many side(use when we want to see which customer got how many orders)
- `many-many` - more like a bridge b/w two tables using fk's(when we want to see products and how many order each product got along with line items)

### join conditions vs where

- with `left join` and a `where` condition on right tables turns out to be an `inner join`
 this is usually used when we deal with reporting of bugs

### Duplicate rows

- `select Count(*) from table_name where email in( select email from table_name group by email having count(*)>1);`

we usually check the duplicates before performing any joins

### Finding unmatched records

- `select * from table_name left join order on o.cust_id=c.id where o.id IS NULL` used when we want to check the data quality

### WHERE vs HAVING

- `where`
  - used to filter the individual rows before aggregation
  - in finding out of a certain range
  - better go with this when we don't use aggregate functions

- `Having`
  - Used to filter the groups after aggregation
  - when we want to deal with aggregate functions
  - better go with this when we want to work on grouped data

`combinations of where, group by, having and order by`

- normal query - for quick look up - `select * from orders`
- `where` - for admin filter - `select * from orders where status = 'paid'`
- `group by` - for dashboard summaries and charts - `select status, count(*) from orders group by status`
- `order by` - to find the latest changes - `select * from orders order by created_at desc`
- `having` - for alerts and health checks - `select count(*) from orders having count(*) > 100`
- `where + group by` - for report generation - `select customer_id, sum(total) from orders where status = 'paid' group by customer_id`
- `where + order by` - for review queues, biggest first - `select * from orders where total > 100 order by total desc`
- `where + having` - for alerts on a filtered set - `select count(*) from orders where status = 'paid' having count(*) > 100`
- `group by + having` - for repeat customers or duplicate checks - `select customer_id, count(*) from orders group by customer_id having count(*) >= 5`
- `group by + order by` - for leaderboards - `select customer_id, sum(total) as revenue from orders group by customer_id order by revenue desc`
- `having + order by` - rarely useful, sorting one row does nothing - `select count(*) as n from orders having count(*) > 0 order by n`
- `where + group by + having` - for loyal paying customers - `select customer_id, count(*) from orders where status = 'paid' group by customer_id having count(*) >= 5`
- `where + group by + order by` - for top paying customers - `select customer_id, sum(total) as revenue from orders where status = 'paid' group by customer_id order by revenue desc`
- `where + having + order by` - rarely useful, same reason as above - `select count(*) as n from orders where status = 'paid' having count(*) > 0 order by n`
- `group by + having + order by` - for the vip segment - `select customer_id, sum(total) as revenue from orders group by customer_id having sum(total) > 1000 order by revenue desc`
- `all four` - for the monthly vip report - `select customer_id, sum(total) as revenue from orders where status = 'paid' group by customer_id having sum(total) > 1000 order by revenue desc`

### set operations

- `UNION` - gives the rows in both the tables - used for merging
- `Union all` - give the rows on t1 followed by t2 - used to stack up the logs
- `Intersect` - give the rows from the both tables - used for present use cases
- `Except` - gives the tables form either of them

### Windows functions

- this allows use to perform calculations across a set of rows that are related to the current row
- these are used for ranking,aggregate functions and running totals

- `Partition by` - divides the groups into data which helps to fetch easily
- `order by` - it specifies the order of rows with each group

- ``Types of Windows functions``
  - Aggregate - this calculate aggregate over a window of rows while retaining rows
  - Ranking - this provides a ranking to the rows with a partition based
    - rank() - to assign ranks within the groups based on specific order
    - Dense rank() - it assigns the same rank to rows and continue without skipping
    - row number() - gives a unique number so no two rows got the same number with-in the partition

- Focus more on sql joins and improve my way of explanation, focus more on remembering practice sql queries

```Common Practices of sql```

- Retrieving some specific data - select,where
- Filtering and searching of the data - where,like,in
- Combine the related data - Joins
- Calculate business metrics - mathematical functions use case - sum,min,max,count,avg
- Group/to summarize the data - group by, having will always come together
- Inserting of new records/updating of the existing records - Insert / Update
- to delete / to deactivate the status - delete / status updates
- Maintain the transactions consistency throughout the query execution