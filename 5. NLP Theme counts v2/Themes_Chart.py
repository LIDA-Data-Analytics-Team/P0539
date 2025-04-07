import pandas as pd
import plotly.graph_objects as go
import re

keyword_trends_df = pd.read_parquet("keyword_trends_by_theme.parquet")

fig = go.Figure()
buttons = []
themes = keyword_trends_df["Theme"].unique()

##trace

##themes

for theme in themes:
    df_sub = keyword_trends_df[keyword_trends_df["Theme"] == theme]
    keywords = df_sub["Keyword"].unique()
    
    for keyword in keywords:
        df_kw = df_sub[df_sub["Keyword"] == keyword]
        
        fig.add_trace(go.Scatter(
            x=df_kw["Academic_year"],
            y=df_kw["Counts"],
            mode="lines+markers",
            name=keyword,
            visible=False,
            legendgroup=theme,
            hovertemplate=f"<b>{keyword}</b><br>Year.%{{x}}<br>Counts: %{{y}}<extra></extra>"
        ))
        
#Buttons for keyword themes
num_keywords = [len(keyword_trends_df[keyword_trends_df["Theme"] == t]["Keyword"].unique()) for t in themes]

i = 0
for theme, count in zip(themes, num_keywords):
    visibility = [False]*len(fig.data)
    for j in range(count):
        visibility[i + j] = True
    buttons.append(dict(
        label=theme,
        method="update",
        args=[{"visible" : visibility},
              {"title" : f"Keyword Trends for Theme: {theme}"}]
    ))
    
    i += count
##Show all
buttons.insert(0, dict(
    label="Show All",
    method="update",
    args=[{"visible" : [True]*len(fig.data)},
              {"title" : f"All Keyword Trends by Theme"}]
))
    
fig.update_layout(
    updatemenus=[
        dict(
            active=0,
            buttons=buttons,
            direction="down",
            x=1.14,
            xanchor="left",
            y=1.1,
            yanchor="top"
        )
    ],
    title="All Keyword Trends by Theme",
    xaxis_title="Academic Year",
    yaxis_title="Keyword Mentions",
    hovermode="closest",
    height=700
)
     
    
fig.show()