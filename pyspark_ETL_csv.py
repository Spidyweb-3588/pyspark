
# coding: utf-8

# In[2]:


import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import Window
#sparksession 드라이버 프로세스 얻기
spark = SparkSession.builder.appName("sample").master("local[*]").getOrCreate()

df_crash = spark.read.format("csv").option("header","true").option("inferschema","true")\
                .load("C:/Users/jiho3/Downloads/Motor_Vehicle_Collisions_-_Crashes.csv")

#날짜와 시간이 yyyy/MM/dd 와 HH:mm 형식으로 바뀌고, 시간대가 00:00~06:00시에 일어난 사건 중에 지역이 'MANHATTAN'인 곳의 날짜별 시간별 부상자 수, 사망자 수
df_crash_losses=df_crash.withColumn("CRASH_DATE_FORMATTED",F.from_unixtime(F.unix_timestamp(F.col("CRASH DATE"),"MM/dd/yyyy"),"yyyy/MM/dd"))        .withColumn("CRASH_TIME_HH",F.lpad(F.col("CRASH TIME"),5,"0"))        .where(F.col("CRASH_TIME_HH").between("00:00","06:00") & F.col("BOROUGH").isin("MANHATTAN"))        .groupBy(F.col("CRASH_DATE_FORMATTED"),F.col("CRASH_TIME_HH"))        .agg(F.max(F.col("NUMBER OF PERSONS INJURED")).alias("TOTAL INJURED")
            ,F.max(F.col("NUMBER OF PERSONS KILLED")).alias("TOTAL KILLED"))

#날짜별 부상자 숫자 순위를 메기는 컬럼과 날짜별 사망자 숫자 순위를 메기는 컬럼을 생성해서 날짜별 부상자수가 1위거나 사망자수가 1위인 날짜,시간,부상자 수,사망자 수를 나타내는 DataFrame
df_crash_or=df_crash_losses.withColumn("MAX_INJURED_DESC_RN",F.row_number().over(Window.partitionBy(F.col("CRASH_DATE_FORMATTED")).orderBy(F.desc(F.col("TOTAL INJURED")))))               .withColumn("MAX_KILLED_DESC_RN",F.row_number().over(Window.partitionBy(F.col("CRASH_DATE_FORMATTED")).orderBy(F.desc(F.col("TOTAL KILLED")))))               .where((F.col("MAX_INJURED_DESC_RN") <= 1) | (F.col("MAX_KILLED_DESC_RN") <= 1))               .select(F.col("CRASH_DATE_FORMATTED")
                      ,F.col("CRASH_TIME_HH")
                      ,F.col("TOTAL INJURED")
                      ,F.col("TOTAL KILLED"))\
               .orderBy(F.col("CRASH_DATE_FORMATTED")
                       ,F.col("CRASH_TIME_HH"))

df_crash_or.write.format("csv").mode("overwrite")\
           .option("header","true").partitionBy("CRASH_DATE_FORMATTED").save("C:/Users/jiho3/Desktop/spark csv source")

spark.stop()

