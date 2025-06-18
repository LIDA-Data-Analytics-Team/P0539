
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

@st.cache_data
def load_data():
    path = "path_to/bertopic_theme_matches_v6_year.csv"
    df = pd.read_csv(path)
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['Similarity'] = pd.to_numeric(df['Similarity'], errors='coerce')

    df['Group_Type'] = df['Faculty_Group'].apply(lambda x: 'Faculty' if x.startswith('Faculty_Year_') else 'School' if x.startswith('School_Year_') else None)

    fac_match = df['Faculty_Group'].str.extract(r'Faculty_Year_([^_]+(?:_[^_]+)*)')
    sch_match = df['Faculty_Group'].str.extract(r'School_Year_([^_]+(?:_[^_]+)*)')
    df['Group_Name'] = fac_match[0].combine_first(sch_match[0])
    df['Group_Name'] = df['Group_Name'].str.replace(r'_\d{4}$', '', regex=True)
    df['Group_Name'] = df['Group_Name'].str.replace('_', ' ', regex=False)

    return df.dropna(subset=["Year", "Similarity", "Group_Type", "Group_Name"])

df = load_data()

st.title("Theme Trends by Faculty or School")

min_year = int(df['Year'].min())
max_year = int(df['Year'].max())
year_range = st.slider("Select Year Range:", min_year, max_year, (min_year, max_year))

sim_threshold = st.slider("Minimum Similarity Threshold:", 0.0, 1.0, 0.3)

faculties = sorted(df[df['Group_Type'] == 'Faculty']['Group_Name'].unique())
schools = sorted(df[df['Group_Type'] == 'School']['Group_Name'].unique())
themes = sorted(df['Best_Matched_Theme'].dropna().unique())

col1, col2 = st.columns(2)
with col1:
    selected_faculties = st.multiselect("Select Faculties:", faculties)
with col2:
    selected_schools = st.multiselect("Select Schools:", schools)

selected_themes = st.multiselect("Select Theme(s):", themes)

filtered_df = df[
    (df['Year'] >= year_range[0]) &
    (df['Year'] <= year_range[1]) &
    (df['Similarity'] >= sim_threshold)
]

if selected_faculties:
    filtered_df = filtered_df[
        (filtered_df['Group_Type'] == 'Faculty') & 
        (filtered_df['Group_Name'].isin(selected_faculties))
    ]

if selected_schools:
    school_df = df[
        (df['Group_Type'] == 'School') & 
        (df['Group_Name'].isin(selected_schools)) &
        (df['Year'] >= year_range[0]) &
        (df['Year'] <= year_range[1]) &
        (df['Similarity'] >= sim_threshold)
    ]
    filtered_df = pd.concat([filtered_df, school_df])

if selected_themes:
    filtered_df = filtered_df[filtered_df['Best_Matched_Theme'].isin(selected_themes)]

theme_counts = (
    filtered_df.groupby(["Year", "Best_Matched_Theme", "Group_Name"])["Total_Frequency"]
    .sum()
    .reset_index()
)

st.subheader("Theme Frequencies Over Time")

if not theme_counts.empty and not selected_themes:
    st.warning("Please select at least one theme to display.")
elif theme_counts.empty:
    st.info("No matching data found for your current filters.")
else:
    fig, ax = plt.subplots(figsize=(10, 5))
    for theme in selected_themes:
        theme_df = theme_counts[theme_counts["Best_Matched_Theme"] == theme]
        if not theme_df.empty:
            for group in theme_df["Group_Name"].unique():
                line_data = theme_df[theme_df["Group_Name"] == group].set_index("Year")["Total_Frequency"]
                line_data = line_data.sort_index()
                ax.plot(line_data.index, line_data.values, label=f"{theme} – {group}", alpha=0.7)

    ax.set_ylabel("Total Frequency")
    ax.set_xlabel("Year")
    ax.set_title("Themes: " + ", ".join(selected_themes))
    ax.legend(title="Theme – Group", bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig)
