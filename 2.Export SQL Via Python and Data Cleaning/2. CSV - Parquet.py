##Convert to Parquet for quicker/greener computing 

import pandas as pd

df=pd.read_csv("Module_NLP_data_clean.csv", encoding="utf=8")

df.to_parquet("Module_NLP_data_clean.parquet", index=False)

df.head(100)

df=pd.read_csv("CR_Keywords_clean.csv", encoding="utf=8")

df.to_parquet("CR_Keywords_clean.parquet", index=False)


df.head()






