# Streaming Transformations
-----------------------------------
So far we have covered
1. append
2. complete
3. output

- we first read the data, do some streaming transformations and write the data. In streaming world - its readStream and writeStream
- spark internally is a micro batch engine - it works batch by batch (batch can be 1 min of data - it gives a feeling of streaming data)

- There are 2 categories of transformation
1. **STATELESS** - where state is not captured (narrow transformations - filter, select - doesn't have to maintain the previous state) - no need to do aggregations, no need to maintain the state
2. **STATEFUL** - state has to be maintained - we processed 10 microbatches, after 5th microbatch is completed, these results are captured in memory of the executor - we are doing groupby, aggregations, joins or windowing functions (It is maintained in state store - which resides in memory of the executor) - if it grows big it causes OOM error and it can gives us performance issues
   - state store holds the aggregation results for previous micro batches - it holds in executor memory
   - Lets say - Amazon has 300+ million active customers - To maintain history from complete beginning when customers joined Amazon
   - If State store will hold this data - its not feasible to store this much data
   - this is **unbounded** (from the beginning, not a particular time like week, month)
   - **bounded** (1 month interval) - there would be a point where we can clean **state store** but its not possible in unbounded

- **Bounded** (bounded by weekly, monthly, quarterly) - we can most probably use the state store
- **Unbounded** (the data would be more so you might have to use your own solution) - it depends if data is less we can use state store here as well

- Refer update-mode-demo notebook
------------------------------------
1.  when we do aggregation i.e state store is created, internally it do it for micro batch, it will club it together without your intervention. if 5 batches are done, 6th is also done, it will accumulate 6 batches - this is hidden from the user.
2. catalog -> Filestore - DBFS - streaming input folder - input1- upload files - file1.json - file2.json - file3.json
3.  In databricks cluster - Open spark UI - structured streaming - Run ID - check state rows


How to implement your own solution without state store coming into picture
--------------------------------------------------------------------------
- custom function implementation for aggregation which will not trigger state store - improves performance
- Refer update-mode-demo notebook

TRIGGERS IN SPARK STRUCTURED STREAMING
-------------------------------------------
- We have understood if our agg is not time bound, like if there lot of entries in state store, then better not to leverage the state store and develop our custom solution
- we know everything is a microbatch in spark structured streaming - Its not continous but gives a feeling of streaming
- **How big is a microbatch? how is this decided ?**
- **when is the new microbatch triggered**

- Both depends on the kind of trigger you specify.

- **Triggers are applicable to writeStream**
- you can mention like **.trigger(processingTime ='10 seconds')**
- **Types of triggers**
  1. **Unspecified (default one)** - once the first microbatch is completed, it will immediately trigger the next microbatch
     - Lets say you have input folder (file1, file2), then we run the spark streaming application
     - Here there is no file3, so why to trigger empty batch - some kind of optimization happens here it will wait for the file to arrive
  3. **fixed Interval**
     - Each microbatch will start after a certain time
     - Lets say if you specify 5 min as a fixed interval - if previous microbatch is completed in 2 min, it will wait for 3 more min to trigger next batch
     - if previous batch completes in 8 min - it will instantly trigger the next microbatch after completion of previous microbatch provided it has data.
     - where we wish to collect good sizable amount of data and then process
  5. **Available Now**
     - It process the microbatch and then stops automatically by itself
     - .trigger(availableNow=True)
     - Lets say you have file1, file2, file3 in the folder - you invoke availnow trigger, it will process all the files as part of the microbatch and then it will stop
   - Ideally streaming applications will not stop, but here it will stop
   - we can schedule it for every hour and then we can stop.
 
   - In fixed interval - streaming job will hold the resources
   - In available now - streaming job will stop and doesn't hold the resources
 
   - Available now its more like a batch processing but here it will take care of incremental processing automatically
 
  FAULT TOLERANCE IN STREAMING
  ------------------------------------
  - So far we have talked about how is stream processing different than batches
  - challenges involved with streaming
  - streaming is taken in micro batch approach
  - **various sources :** socket source, file source, kafka source
  - **sinks:** file, delta, kafka, console
  - Readstream, processing, writeStream
  - **checkpoint**- maintain the state (calculating the runningtotal), it maintains info on what all it processed
  - **output modes** - append, complete, update
  - **state store** - maintain the state in executor memory
  - **foreach** - where we write our own custom logic - we don't use state store here
 -  How to avoid state store and implement our own logic
 -  **Types of triggers** - unspecified, availableNow, fixed interval
 -  **Types of aggregations** -
   1.Time bound aggregations(also called window aggregations)
    1. Tumbling window
    2. sliding window
   2.continous aggregations

#### Fault tolerance and exactly once guarantee
-----------------------------------------------
- Ideally a Streaming application should run forever
- It might stop
  1. Exception (whenever we get corrupt data, we haven't handled, application can stop)
  2. Maintenance activities (server upgrade, rewrite the code)
     
- our application should be able to stop and restart gracefully, this means to maintain **exactly once semantics**
- **Exactly once semantics (do not miss any input record, do not create duplicate output records)**
- Spark structured streaming provides ample support for this exactly once sementics
- It maintains the state of the microbatch in the checkpoint location
- checkpoint location helps to achieve fault tolerance
- **checkpoint location mainly contains 2 things**
  1. **read position** - which all files have processed
  2. **state information** - calculating running total

- Spark structured streaming maintains all the info it requires to restart the unfinished microbatch
  
- **To guarantee, exactly once sementics, there are **4** requirements should be met**
  1. **Restart the application with same checkpoint location** - lets say we got an exception in 3rd batch, in commits we would have 2 commits.
  2. **use a replayable source** - consider there are 100 records in the third batch, after processing 30 records it gave some exception, these 30 records should be available to you when you start reprocessing (when we use socket datasource we can't get older data back again)
   - Kafka, file source both are replayable sources
 3. **Use deterministic computation** -  when we start reprocessing, these 30 records it should give the same output (30 record processed earlier and 30 rec processing now after restart) ex: square root of 4 result same any time we calculate - today, tomorrow, forever, $ rate changes everyday
4. **Use an Idempotent sink** - any number of times you run the application the output should be same
     - Consider there are 100 records in the 3rd microbatch
     - after processing 30 records, it gave some exception
     - we are processing 30 records 2 times, after restart, we are writing this to output 2 times
     - 2nd time when you are writing the same output, it should not impact us
     - Either it should discard the 2nd output or it should overwrite the 1st output with the 2nd outpu

#### Types of aggregations 
-----------------------------
- There are 2 types of aggregations
  1. Timebound aggregations
  2. continous aggregations
 
- **continous aggregations:**
- you purchase some grocery from a retail store
- on purchase of 100 rs you get 1 reward point
- if these reward points never expire (unbounded)
- If there are 100 million customers (state store has to keep 100 million records), lets say every month this retail store is getting 1 million new customers,state store is getting bigger - history in the state store will keep on growing.
- In such cases, its better to implement custom solution which we have implemented earlier

- **Timebound aggregations(window aggregations)**
- one month window (I want to calculate the reward points over a window of 1 month, after that do not need to maintain the state store, this make sure state store won't grow too much.)
- Lets say reward points expire in 1 month
- state store cleanup will take place each month
- There are 2 kinds of window
  1.**Tumbling window - a series of fixed size, non overlapping time interval**
     -  Ex: 10 -10.15
     -  10.15 - 10.30
     -  10.30 - 10.45
     -  Here we have a fixed time
  3. **sliding window - a series of fixed size, overlapping window (15 min window, sliding interval is 5 min)**
     - 10 - 10.15
     - 10.05 - 10.20
     - 10.10 - 10.25
  - **The aggregation windows are based on event time not on triggered time**
  - **Event time** - is the time event is generated
  - **Triggered time** - event will reach to us for processing (lot of delays can happen like network delays), this is called triggered time
 
  - suppose, we have this events, In this image, event is generated at 11.05 and this event might reach to spark at 11.20
  - <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/2cd00ed5-87e6-48fd-a3f3-43e6663cf0fc" />

  - Business has asked us to find sales every 15 minutes, we should use tumbling window
  - Ex: 11 - 11.15
  - 11.15 - 11.30
  - 11.30 - 11.45
  - 11.45 - 12
  - Let's try to execute this and calculate this, using spark structured streaming
 
  - Here we are using socket as source, and console as output
  - open a localhost netcat : nc -lk 9970
  - Refer **prog2.py file**
  - <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/35740aab-97b3-40a4-9520-ce09697da7ac" />
  - state store window will be like this after inserting the records, check late arriving records also they will get updated in that respective window because not cleaning up previous windows accomodate updates for late arrriving records, if we don't know when a record will be late 1 year, 1 month so we can't cleanup state store and keeps growing again and leads to OOM error .
  - <img width="363" height="300" alt="image" src="https://github.com/user-attachments/assets/661c65f8-6735-4212-8e65-24902d7a6943" />

  #### How to solve the above challenge using Watermark Streaming (How to deal with late arriving records)
  ----------------------------------------------------------------------------------------------------------
  - previously, we looked into windowing aggregations and we wouldn't able to cleanup the state store because of some late arriving records
  - If we keep entertaining the late arriving records, we can't clean state store
  - To deal with late coming records, we have a concept of **watermark**
  - **Watermark** : It is like setting an expiry date to a record  
  - Lets say watermark duration is 30 min, if a record comes after 30 min then spark can discard that  
  - If we don't go in this mode, we should maintain full history there should be some constraint - till this time we can wait, after that we can ignore  
  - Lets say business might say 99.99% accuracy, but we know 99.9% of your records are never late than 30 minutes  
  - Then you can set your watermark to 30 minutes  
  - out of 1000 events, 1 event can arrive later than 30 minutes - we can ignore  
  - 999 events will arrive within 30 minutes which we will accomodate  
  - Refer prog2.py file  
  - watermark should be added before groupby only  
  - At every point of time a **watermark boundary** will be created - whatever is the latest event till now - 30 minutes  
  - <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/127e4e1d-792b-40b8-ba78-8644465dc399" />  
  - Latest event is 11:05, -30 minutes is 10.35 is the watermark boundary, any record before 10:35 is discarded from state store  
  - Eventhough some of the records were more than 30 min they weren't discarded, some of the records were more than 30 min, those are not discarded it all depends on which window is open  
  - **Points to remember**  
  1. Watermark is the way to clean state store  
  2. Events within the watermark are taken - this is guaranteed  
  3. Events outside the watermark may or may not be taken - depends on which window open

#### Watermark and output modes (update mode is recommended and efficient one)
------------------------------------------------------------------------------
- Even output mode has a relation to the watermark
- There are 3 output modes - 1)complete 2) update 3) append
- complete mode  with watermark doesn't work
- complete mode doesn't allows us to clean state store
- Make only a small change in prog2.py
- <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/fac32e91-0388-4639-b974-bf36c99b0fc7" />
- If we put this 11:14 record -
- <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/c39877c2-819d-488a-8e92-6ec1098b730f" />
- Eventhough we used a watermark with complete mode - it didn't work - complete mode isn't recommended
- <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/9b297fb6-329d-46f1-a5e7-4b27ef6efd80" />

###### Append mode 
- For aggregations and window aggregations append mode will not work
- watermark with windowing aggregations there is a big change in scenario
- For append mode, if we use watermark 30 min duration - windowing aggregations are allowed
- <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/a114c23c-cf17-43b6-bde5-1d1c4fd449be" />
- <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/a9ff8c87-7233-4e2c-8e39-231f9e380cdd" />
- watermark window is 10.35
- if we put 11.05 record : it comes under 11-11.15 window, this record isn't outside the window, but its not inserted immediately, its maintained in the state store, may be more updates can happen to it and will not put to console
- In append mode, only when the particular window is expired, then only it will show up in console
- It delays the output to write it to sink only when the window is expired, then only it can guarantee no further updates to the record
- **The window information will only be printed, once this window expires**
- we have to wait atleast watermark duration - only disadvantage with append window

##### Sliding window (Fixed size + overlapping windows)
- 11:00 - 11.15
- 11:05 - 11.20
- 11.10 - 11.25
- Add one more parameter sliding parameter
- <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/4a05db67-9fee-48e3-983e-a8e8d914a846" />

#### Streaming Joins (Joins of static df + streaming df and joins of 2 streaming df)
----------------------------------------------------------------------------------
- 












































