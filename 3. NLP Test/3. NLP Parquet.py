##Simple NLP to test the file

import pandas as pd

modules = pd.read_parquet("Module_NLP_data_clean.parquet")

themes = pd.read_parquet("CR_Keywords_clean.parquet")

##Group ketwords by theme

themes_keywords = {
    col:themes[col].dropna().str.lower().tolist()
    for col in themes.columns
}

##count themes

import re
def count_theme_matches(text, keywords):
    if not isinstance(text, str):
        return 0
    words = re.findall(r'\b\w+\b', text.lower())
    return sum(word in keywords for word in words)


for theme, keywords in themes_keywords.items():
    modules[f"{theme}_hits"] = (
        modules['Module_Syllabus'].apply(lambda x: count_theme_matches(x, keywords))+
        modules['Module_Objectives'].apply(lambda x: count_theme_matches(x, keywords))
    )

##Print temporal trends

trends = modules.groupby("Academic_year")[[col for col in modules.columns if col.endswith("_hits")]].sum()
display(trends)






