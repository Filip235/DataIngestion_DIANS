from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, StructType

KAFKA_TOPIC = "stock_prices"
KAFKA_BROKER = "localhost:9092"

# Initialize Spark Session with Kafka package

spark = SparkSession.builder \
    .appName("KafkaSparkStreaming") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.1") \
    .getOrCreate()


# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()

# Convert Kafka DataFrame
stock_data = df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)").toDF("ticker", "price")

# Print the streaming data
query = stock_data.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
