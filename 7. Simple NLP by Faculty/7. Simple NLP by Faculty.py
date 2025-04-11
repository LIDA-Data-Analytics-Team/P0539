##Simple NLP of themes/keyword counts over time by Owner Faculty

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

module_df = pd.read_parquet("module_nlp.csv")
keywords_df = pd.read_parquet("CR_keywords.csv")

keywords_df_t = keywords_df.transpose()
theme_keyword_map = {
    theme: keywords_df_t.loc[theme].dropna().tolist()
    for theme in keywords_df_t.index
}

module_df["Combined_Text"] = (
    module_df["Module_Syllabus"].fillna("") + " " +
    module_df["Module_Objectives"].fillna("")
).str.lower()

def count_keywords(text, keywords):
    return sum(bool(re.search(rf"\b{re.escape(keyword.strip().lower())}\b", text)) for keyword in keywords)

for theme, keywords in theme_keyword_map.items():
    module_df[theme] = module_df["Combined_Text"].apply(lambda text: count_keywords(text, keywords))

theme_columns = list(theme_keyword_map.keys())
melted_df = module_df.melt(
    id_vars=["Academic_year", "Module_Owner_Faculty"],
    value_vars=theme_columns,
    var_name="Theme",
    value_name="Count"
)

grouped_df = melted_df.groupby(
    ["Academic_year", "Module_Owner_Faculty", "Theme"], as_index=False
).sum()

faculties = grouped_df["Module_Owner_Faculty"].unique()
fig = make_subplots(rows=len(faculties), cols=1, shared_xaxes=True, subplot_titles=faculties)

for i, faculty in enumerate(faculties, start=1):
    faculty_data = grouped_df[grouped_df["Module_Owner_Faculty"] == faculty]
    for theme in faculty_data["Theme"].unique():
        theme_data = faculty_data[faculty_data["Theme"] == theme]
        fig.add_trace(
            go.Scatter(
                x=theme_data["Academic_year"],
                y=theme_data["Count"],
                mode="lines+markers",
                name=theme,
                legendgroup=theme,
                showlegend=(i == 1)
            ),
            row=i, col=1
        )

fig.update_layout(
    height=300 * len(faculties),
    title="Theme Mentions Over Time by Faculty",
    xaxis_title="Academic Year",
    yaxis_title="Keyword Count"
)

fig.write_html("theme_mentions_over_time_by_faculty.html")