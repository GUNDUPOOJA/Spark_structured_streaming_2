from pyspark.sql.functions import *
from pyspark.sql import SparkSession

if __name__ == '__main__':

    print("Creating Spark Session")

    spark = SparkSession.builder \
            .appName("streaming application") \
            .config("spark.sql.shuffle.partitions",3) \
            .master("local[2]") \
            .getOrCreate()
    
    transactions_schema = 'card_id long, amount long, postcode long, pos_id long, transaction_dt timestamp'

    #1. read the data
    transactions_df = spark.readStream \
                 .format("socket") \
                 .option("host","localhost") \
                 .option("port", "9972") \
                 .load()
    
    value_df = transactions_df.select(from_json(col("value"), transactions_schema).alias("value"))
    
    refined_transactions_df = value_df.select("value.*")

    refined_transactions_df.printSchema()

    
    member_df = spark.read.format('csv') \
                 .option("header", True) \
                 .option("inferSchema", True) \
                 .option("path","/Users/trendytech/Desktop/member_details.csv") \
                 .load()

   #define join condition now

    join_expr = refined_transactions_df.card_id == member_df.card_id

    join_type = "inner"

   # card_id will appear 2 times, so drop it
    enriched_df = refined_transactions_df.join(member_df, join_expr,join_type).drop(member_df["card_id"])


    query = enriched_df \
        .writeStream \
        .format("console") \
        .outputMode("update") \
        .option("checkpointLocation","checkpointdir1") \
        .trigger(processingTime = "15 seconds") \
        .start()