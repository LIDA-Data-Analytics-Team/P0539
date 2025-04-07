
import pandas as pd

import re

nltk.data.path.append(r'/nltk_data')

df = pd.read_parquet("Module_NLP_data_clean.parquet")

themes_df = pd.read_parquet("CR_Keywords_clean.parquet")

def clean_phrase(phrase):
    return re.sub(r'[^a-zA-Z\s]', '', phrase).lower().strip()

theme_keywords = {}
for theme in themes_df.columns:
    cleaned = themes_df[theme].dropna().astype(str).apply(clean_phrase)
    theme_keywords[theme] = [kw for kw in cleaned if kw]
    
def count_theme_matches(text, keywords):
    if not isinstance(text, str):
        return 0
    text_clean = clean_phrase(text)

    return sum(1 for phrase in keywords if phrase in text_clean)

for theme, keywords in theme_keywords.items():
    df[f"{theme}_hits"] = (


df["Module_Syllabus"].apply(lambda x: count_theme_matches(x, keywords)) +
df["Module_Objectives"].apply(lambda x: count_theme_matches(x, keywords))
    )
    
trends = df.groupby("Academic_year")[[col for col in df.columns if col.endswith("_hits")]].sum()

display(trends)
    
