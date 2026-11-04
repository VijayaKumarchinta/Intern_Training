# Pandas

## Name comes from "panel data" (an econometrics term) - also a pun on Python Data Analysis

- an open-source library designed for data manipulation and analysis
  - built on top of NumPy, helps to handle datasets that fit in memory for data cleaning, transformation and analysis
  - can integrate with NumPy, Matplotlib and scikit-learn
- ``Data structures``:
  - `Pandas Series`:
    - one-dimensional labelled array (like one column)
    - we use when there is a single column with index
    - In real time we use in DA,ML preprocessing,ETL scripts
  - `Pandas DataFrame`:
    - two-dimensional table of rows and columns (like an Excel sheet)
    - we use when we deal with excel sheets
    - In real time we use everywhere when we are dealing with rows columns
- ``Basic operations``:
  - Data I/O - read and write CSV, Excel, JSON and SQL data
  - Cleaning - handle missing values (`.dropna()`, `.fillna()`), remove duplicates, fix inconsistencies
  - Transformation - can filter, sort, group, merge & modify the data
  - Visualization - helps to visualize the data quickly with built-in plots
- ``Index``
  - Labels for rows and helps for fast lookups,auto alignments

### Quick check first whenever we are given a data

- `df.head()` - helps to see the first rows
- `df.shape` - helps to see the no.of rows and columns
- `df.info()` - tells you what data we got
- `df.describe()` - Provides a statistical summary of the dataset
- `df.isna().sum()` - helps to find out no.of missing values per column
- `df.dtypes` - tells you the data types per column

### DataFrames

- `creating data frames`
  - From a dictionary:
    - where keys becomes columns,values becomes rows, useful when we dealing with quick tests
      - `pd.DataFrame()` - creates a df from dictionary
      - `pd,to_datetime()` - converts values into datetime format
      - `print()` - helps to display data frames
  
  - From a list of dictionary:
    - where each dictionary acts as rows, keys acts as columns and helps to match with json responses
  
  - From a file:
    - can read,write any type of files and where the real data lives when we are dealing with any sort of projects
      - `pd.read_csv()` - helps to read data from csv
      - `df.to_csv()` - helps to write data to cs file
      - `df.head()` - helps t0 display the first rows by default

- `Index`
  - helps to label the rows and for fast lookup
    - `df.index` - helps to access the index
    - `df.set_index()` - helps to set columns as df index
    - `df.reset_index()` - helps to revert back the changes
    - `df.index.is_unique - check the uniqueness of the index

- `Accessing and selecting` - involves retrieving,exploring and manipulating of data which is being stored
- use colon `[:]` to select all rows and specific columns
  - `df["column"]` - accessing a single column and return as series
  - `df["col1","col2"]` - accessing multiple columns and return as data frame
  - `df.loc[rows,cols]` - label-based selection for clear and safe selection inclusively
  - `df.iloc[rows,cols]` - position-based selection exclusively
  - `df.head()/df.tail()` - used for first and last n rows
  - `df.at[row,col]` - helps to access the specific cell

- `Filtering with multiple conditions`
  - can filter using .loc[],numpy,query
    - boolean marks - it helps to combine the conditions more like sql where clause this comes within the .loc[]
    - `df.query()` - filter the rows with a readable strings
    - `df["col"].isin()` - filter values using a list same like sql IN
    - `df["col"].between()` - used to filter for inclusive ranges same as sql between
    - `df["col"].str.contains()` - to find out text pattern
    - `df["col"].isna()/df.notna()` - to find out missing values same like IS NULL

- `Slicing` - an important skill helps for extracting specific data into subsets
  - common methods are
    - `df.iloc[]` - integer-based indexing
    - `df.loc[]` - label-based indexing

- `Sorting` - Helps to organize and structure the information for easier decision making
  - `df.sort_values()` - by(row),ascending(a boolean),inplace(swaping with new df if original is modified),na_position(controls the nana values),ignore_index(resets the index)
  - `df.sort_index` - a method which sort the df in ascending order w.r.t the index
  - can be done while choosing the sorting algorithms within the `sort_values` by adding the kind of algorithm under `kind` parameter

- `Merging,joining,concatenating`
  - `Concatenating` - combining two data frames as one final df either by stacking them up or placing side by side
    - `using .concat()` - after creating 2 df's we can concat() them using this method
    - `using axes` - where it prints all columns by setting up  `sort = False` in `.concat()`
    - `using ignoreindex` - where it set up `ignore_index=true` in `.concat()`
  
  - `Merging` - it is similar to SQL joins
    - `using pd.merge` - with help of keys we can merge by passing key parameter to the `.merge()`
    - `using how argument in the .merge()`
      - `how=left` - left outer join = keys from left frame only
      - `how=right` - right outer join = keys from right frame only
      - `how=outer` - full outer join = use union keys for both the frames
      - `how=inner` - inner join = use intersection keys fro both the frames
  - `joining` - same as merge but name is different we `pd.join()`

- `Pivot tables` - a statistical table that summarizes a the dat like big datasets
  - this got three arguments:
    - index - column names
    - values - what we want to show
    - aggfunc - aggregation functions

- `main thing was these always create while grouping the values so it contains no duplicates it will give the combine result in tha table`

### Series

- `creating series`
  - by default we create a series from numpy array pandas and it automatically assigns a numeric index starting 0.
  - can be created by warping numpy in the series to create pandas series

- `Accessing Elements` - elements will be accessed using index values
  - `slicing`
    - where we use colon before the number so that we can access till that range exclusively - used for first elements to retrieve
      - Ex: sr[:5]
    - where we use colon after a negative number to retrieve the last numbers
      - Ex: sr[-10:]

- `Binary operations`
  - this involves in applying mathematical/logical operations on data frames/series to produce new results
    - `Arithmetic operations` - addition,subtraction,multiplication and division
    - `Comparison Operations` - equal to, not equal to, greater than, less than
    - `Logical operations` - And, or, not

- `Indexing`
  - the series.index attribute allows us to get/set te index labels of a series object
    - `series.index` - helps to access the elements
    - `series.index = new_index` - helps to modify the assigned indexes

### Data input/output - pandas got various functions to read and write the data to different files

- `CSV`
  - stands for `Common-Separated Values` which allows us to store the data in tabular format
  - `to read the data in csv` - `pd.read_csv(filepath,sep=',',header='infer',index_col=None,usecols=None,engine=None,skiprows=None,nrows=None)`
  - `to read specific columns` - `pd.read_csv("file_name"usecols=["col_name"])`
  - `setting of specific index` - `pd.read_csv("file_name",index_col="col_name")`
  - we can handle missing values using read_csv by passing `na_values=["N/A"]` to the it
  - we can limit the reading of rows using read_csv by passing `nrows=n` to it
  - we can create/write the data using `df.to_csv("file_name)`

- `JSON`
  - stands for `javascript object notation` which allows us to store the data in key-value pairs
  - `to read the data in json` - `pd.read_json("file_name")`
  - `when we are working with nested json` - use `pd.json_normalize()` along with
  - `Converts a response to python dictionary` - `response.json()`
  - `fetch data from the url` - `request.get(url)`
  - `want to export df to json file` - `df.to_json("file_name")`
    - `json.dump()` - used to write python obj to json file directly
    - `json.dumps()` - convert python obj to json strings
    - `json.load()` - used to read json and convert it into python obj
    -`json.loads()` - convert json string to python object

### Data Cleaning - Where we ensure accuracy and consistency in preprocessing

- ```Missing data```
  - occurs when the data is not collected these are represent as:
    - None - a python obj represent missing values
    - NaN - a special float value from numpy recognized by all systems

  - ``Checking out the missing values``
    - `df.isnull()` - this returns a boolean value where true = missing data
    - `df.isna()` - same as `.isnull`

  - ``Filling out the missing data``
    - `df.fillna()` - used to replace the NaN with the given values mostly `0` and limit to nulls,nan's
      - by passing `method='pad'` it helps to fill with pervious value
      - by passing `method='bfill'` it helps to fill with next value
    - `df.replace()` - when we want to replace specific value present in the table

  - ``Dropping out the missing values``
    - `df.dropna()` - used to remove rows with at least one missing value
      - by passing `how='all'` we can remove rows where all values are missing
    - `df.dropna(axis=1)` - used to remove columns with at least one missing value

- ```Removing duplicates```
  - `df.drop_duplicates()` - a method designed to remove the duplicate rows from data frames based on columns
    - by passing `subset` we can able to drop duplicates from specific columns
    - by passing `keep` we can able retain the occurrences of duplicates
    - by passing `inplace` we can directly do changes to the existing df without created a new one

- ```String manipulation```
  - refers to cleaning,Transforming and processing the text data so it became suitable for analysis
  - `.str.lower()` - converts every character to lowercase
  - `.str.upper()` - every character to uppercase
  - `.str.strip()` - removes unwanted white spaces
  - `.str.split()` - spilt each string into list based on given separator
  - `.len()` - calculates the length of each string per column
  - `.cat()` - concatenates all strings into a single column based on given separator
  - `.startswith()/endswith()` - checks whether the string starts with specific prefix/ends with specific suffix

### Data Processing

- A process of manipulating,Transforming and analyzing the data using python
  - changes raw -> structured data -> meaningful insights for analyzing,visualization
  
  - `Loading of data(pd.read_csv)` -> `printing of data(df.head()/df.tail())` -> `then columns(df.columns)` -> `then summary of the data(df.info)` -> `finding the missing values(df.isnull())` -> `removing the missing values(df.dropna())` or `filling of missing values(df.fillna())` -> `manipulating rows and columns(df.drop().head())` -> `sorting the values(df.sort_values())` -> `Visualize the dataFrame(df.plot(x='name on x axis',y=name on y axis))`

### Data Normalization

- Process of scaling numeric features to a standard range,preventing large values from dominating the learning process in ml models
- this helps to improve the algorithm performance
  - to avoid numerical instability\
  - ensure all features contributes equally
- Steps:
  - ```Import libraries -> load/create a dataset -> apply normalization techniques -> visualize the results```

- ```Techniques of normalization```
  - `Maximum absolute scaling`:
    - This rescales each feature b/w -1 and 1 by dividing all values by absolute maximum value in that particular column and useful when the given data doesn't consist of negative values
      - `max[column] = max[column]/max[column].abs().max()`
  
  - `Min-Max Scaling`:
    - rescales the features to a hard and fast range of[0,1] by subtracting the min values then divides by range
    - works well with `KNN`
      - `scaled[column]=(scaled[column] - scaled[column].min()) / (scaled[column].max() - scaled[column].min())`
  
  - `Z-score method`:
    - Known as standardization where it changes the values in each column so they have mean of 0 and SD of 1.
    - best when we follow normal distribution
      - `z_scaled[column] = (z_scaled[column] - z_scaled[column].mean()) / z_scaled[column].std()`

### Data Manipulation

- Involves in creating,modifying and analyzing the datasets using pandas
- helps to clean and prepare data for further tasks
  - Steps:
    - `Creating df(pd.DataFrame())` -> `adding rows to df(pd.concat())` -> `getting the shape and info of the data(df.shape() and df.info())` -> `selecting df(df["col_name"])` -> `filtering the data` -> `sorting of data(df.sort_values)`

### Grouping and aggregating with pandas

- these are helps to summarize large datasets by dividing records into meaningful groups and calculating statistics
  - pandas provides
    - group by() and aggregate functions:
      - to organize records based on one/more columns
      - to calculate total,avg, min, max and count
