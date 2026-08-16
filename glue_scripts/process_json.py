import sys

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType


args = getResolvedOptions(
    sys.argv,
    [
        "SOURCE_BUCKET",
        "OBJECT_KEY",
        "OUTPUT_BUCKET"
    ]
)

spark = SparkSession.builder.getOrCreate()

input_file = (
    f"s3://{args['SOURCE_BUCKET']}/{args['OBJECT_KEY']}"
)

output_path = (
    f"s3://{args['OUTPUT_BUCKET']}/json/"
    f"{args['OBJECT_KEY'].replace('/', '_')}/"
    
)

country_mapping = {
    "India": "IN",
    "USA": "US",
    "Canada": "CA",
    "Australia": "AU"
}


def get_country_code(country):

    return country_mapping.get(
        country,
        "UNKNOWN"
    )


country_udf = udf(
    get_country_code,
    StringType()
)

dataframe = spark.read.json(
    input_file
)

dataframe = dataframe.withColumn(
    "country_code",
    country_udf(dataframe["country"])
)

dataframe.write.mode("overwrite").json(
    output_path
)