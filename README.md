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


