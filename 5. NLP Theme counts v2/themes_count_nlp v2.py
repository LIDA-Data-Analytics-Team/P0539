
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

nltk.data.path.append(r'I:/P0539/CSVs/nltk_data')

df = pd.read_parquet("C:/Users/medlwha/Documents/NEW/Module_NLP_data_clean.parquet")

themes_df = pd.read_parquet("C:/Users/medlwha/Documents/NEW/CR_Keywords_clean.parquet")

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

##keyword breakdown start

keyword_counts = []

for theme, keywords in theme_keywords.items():
    for keyword in keywords:
        col = f"{theme}_{keyword}_counts"
        df[col] = (
            df["Module_Syllabus"].apply(lambda x: count_theme_matches(x, keywords)) +
            df["Module_Objectives"].apply(lambda x: count_theme_matches(x, keywords))
        )
        keyword_counts.append((theme, keyword, col))
        
keywords_trend_data = []

for theme, keyword, col in keyword_counts:
    grouped = df.groupby("Academic_year")[col].sum().reset_index()
    grouped["Theme"] = theme
    grouped["Keyword"] = keyword
    grouped = grouped.rename(columns={col:"Counts"})
    keywords_trend_data.append(grouped)
    
keyword_trends_df = pd.concat(keywords_trend_data)

keyword_trends_df.to_csv("keyword_trends_by_theme.csv", index=False)
        
##keyword breakdown end

display(trends)
    
