
from pyspark.sql.functions import *
from pyspark.sql import SparkSession

if __name__ == '__main__':

    print("Creating Spark Session")

    spark = SparkSession.builder \
            .appName("streaming application") \
            .config("spark.sql.shuffle.partitions",3) \
            .master("local[2]") \
            .getOrCreate()
    
    orders_schema = 'order_id long, order_date timestamp, order_customer_id long, order_status string'

    #1. read the data
    orders_df = spark.readStream \
                 .format("socket") \
                 .option("host","localhost") \
                 .option("port", "9970") \
                 .load()
    
    #orders_df.printSchema() #Every thing is string here

    # eventhough we thought its a json, but the value of every column is string
    # we have to use some json utility to parse this string into a json, so that we can extract some columns here

    value_df = orders_df.select(from_json(col("value"), orders_schema).alias("value"))
    
    refined_orders_df = value_df.select("value.*")

    refined_orders_df.printSchema()

    window_agg_df = refined_orders_df  \
                    ## .withWaterMark("order_date","30 minutes") \
                       .groupBy(window(col("order_date"),"15 minutes")) \
                    .agg(sum("amount").alias("total_invoice"))

    window_agg_df.printSchema()  


    output_df = window_agg_df.select("window.start", "window_end","total_invoice")


    output_df \
        .writeStream \
        .format("console") \
        .outputMode("append") \
        .option("checkpointLocation","checkpointdir1") \
        .trigger(processingTime = "15 seconds") \
        .start()