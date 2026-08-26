from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(__import__('sys').argv, ["JOB_NAME", "SOURCE_PATH", "TARGET_PATH"])
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

orders = spark.read.option("header", True).csv(args["SOURCE_PATH"])
curated = (
    orders
    .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
    .withColumn("order_date", F.to_timestamp("order_date"))
    .withColumn("status", F.upper(F.trim("status")))
    .filter(F.col("order_id").isNotNull())
    .filter(F.col("amount") >= 0)
    .dropDuplicates(["order_id"])
    .withColumn("order_year", F.year("order_date"))
    .withColumn("order_month", F.month("order_date"))
)

(curated.write.mode("overwrite")
    .partitionBy("order_year", "order_month")
    .parquet(args["TARGET_PATH"]))

job.commit()
