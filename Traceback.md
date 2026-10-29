# Traceback in python

- Traceback:
  - a report of the chain of function calls that was active when an exception was raised
  - Used when we want to know where the error happened and how the program go there

- Traceback module:
  - an interface to extract, format and prints these stack traces from our own code
  - used when we wants to show the traceback without crashing in python

- Syntax:  
  - Traceback for the recent call
  - location of the program
  - in which line error was encountered
  - name of the error

- the tracebacks come from:
  - caught exceptions - `can be accessible via sys.exc_info()`
  - uncaught exceptions - `automatically stored in sys.last_traceback and return a tuple with three items(type,value,it's object)`

## Traceback Functions

- `Printing`: helps to print to a file
  - ``.print_tb()``:
    - prints only stack frames from the traceback object
    - used when we want to print the error msg but only the call path
  
  - ``.print_exception(e)``
    - prints the given exception
    - used when we want to print the exception error outside the expect block
  
  - ``.print_exc()``
    - prints the traceback of the exception which is currently being   handled usually used in except
    - when we want to see the full error with out being crashed
  
  - ``.print_last()``
    - prints the last exception that reached the prompt
    - used when we want to see the last uncaught error
  
  - ``.print_stack()``
    - prints the current call stack
    - used when we want show the current call stacks

- `Formatting` - instead of printing it will returns as the string/list of strings so we use joined frames to extract easily `` ''.join(),end='' ``
  - ``.format_exc()``
    - returns the entire except traceback as a single string
    - used when we want full traceback as a string format
  
  - ``.format_exception()``
    - returns a list of strings
    - used when we want a full traceback text as stored exception
  
  - ``.format_exception_only()``
    - returns only the exception type and the message
    - used for one-line log
  
  - ``.format_tb()``
    - returns only stack frames as a list of strings
    - used when we want to see the frames as text

  - ``.format_stack()``
    - returns the current call stack as a list of strings
    - used when we want to see where the call came from
  
  - ``.format_list()``
    - formats a list of frame_summary objects into strings
    - used when we want to print the filtered frames

- `Extracting` - helps to return the data in structured format(stack_summary)
  - we use extract when we want data to filter/to build json logs
  - ``.extract_tb()``
    - helps to extract the traceback object and returns frame data
    - used when want frame data as json logs
  
  - ``.extract_stack()``
    - helps to extract from the current call stack
    - used when we want to record where something was created

- `Walking` - helps to iterate over frames
  - we use walk when we want to analyze the data inside the frames
  - ``.walk_tb()``
    - helps to inspect the exception call path
  
  - ``.walk_stack()``
    - helps to inspect the execution from a point outward

### Traceback classes

- `TracebackException class`:
  - this will create an object from the actual exceptions to capture the data which is used for later printing
  - This class contains the following attributes:
    - stack - where helps to summarize the frames
    - exc_type - helps to show the exception type
    - __cause__/__context__ - helps to TracebackException the original
    - filename,lineno,text,offset,msg - more like an extra and detailed structure of an syntax error
  
- `StackSummary Class`:
  - This class represent a call stack ready which is ready for formatting
    - `.extract()` - helps to build from a frame generators like walk_tb()/walk_stack()
    - `.from_list()` - this will use FrameSummary objects to build StackSummary objects in the form of list of tuples
    - `.format()` - this will return a list of strings one

- `FrameSummary Class`:
  - This will represent a single frame in a traceback

in one line:
  ```Traceback is the call-stack record attached to the exception that are logged along with req context to find out cause of errors in monitoring```

### Most commonly used

- `logging.exception("msg")` inside except, then a bare `raise` - logs the full traceback and re-raises so the original traceback is kept
- `format_exc()` - full traceback as a string for alerts, emails
- `format_exception(e)` - full traceback text of stored/async exceptions
- `format_exception_only(e)` - one-line error for logs
- `extract_tb(e.__traceback__)` - frame data for json logs, hiding library frames
- `TracebackException` - capture an error now, format it later
- never show tracebacks to end users, and filter local variables before logging

- ```Traceback - when we want to extract and format the exception information```(Exception analysis - helps to inspect what went wrong)
  - we use this after an exception occurs
  - primary use cases are generating the error reports,stack inspection  

- ```Trace - when we want  to monitor and record program execution```(Execution monitoring - helps to inspect what our program does)
  - we use before/during execution
  - primary use cases are debugging, execution tracing