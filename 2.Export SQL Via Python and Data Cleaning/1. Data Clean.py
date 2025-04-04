
import pyodbc
import pandas as pd
print(pyodbc.drivers())
import re

conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=.....;"
            "DATABASE=....."
            "UID='User_name';"
            "PWD='password';"
)

query = "SELECT*FROM dbo.vm_Module_NLP_data"

df = pd.read_sql(query,pyodbc.connect(conn_str))

df.to_csv("Module_NLP_data.csv", index=False, encoding="utf=8")


df = pd.read_csv("Module_NLP_data.csv", encoding="utf=8")

def clean_text(text):
    if not isinstance(text, str):
        return text
    text = text.lstrip("=")
    text = re.sub(r"[^A-Za-z\s]", "", text)
    text = re.sub(r"zs+", " ", text)
    return text.strip()

columns_clean = ['Module_Syllabus', 'Module_Objectives']

for col in columns_clean:
    if col in df.columns:
        df[col] = df[col].apply(clean_text)
        
df.to_csv("Module_NLP_data_clean.csv", index=False, encoding="utf-8")


##drop duplicates

df = pd.read_csv("Module_NLP_data_clean.csv", encoding="utf=8")

df = df.drop_duplicates()

df.to_csv("Module_NLP_data_clean.csv", encoding="utf=8")


## Clean keywords

df = pd.read_csv("C:/Users/medlwha/Documents/NEW/CR_Keywords_str7.csv", encoding="utf=8")

def clean_text(text):
    if not isinstance(text, str):
        return text
    text = text.lstrip("=")
    text = re.sub(r"[^A-Za-z\s]", "", text)
    text = re.sub(r"zs+", " ", text)
    return text.strip()

columns_clean = ['Module_Syllabus', 'Module_Objectives']

for col in columns_clean:
    if col in df.columns:
        df[col] = df[col].apply(clean_text)

#Save
        
df.to_csv("CR_Keywords_clean.csv", index=False, encoding="utf-8")






