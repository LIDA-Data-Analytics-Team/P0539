##Organic BERT topic modelling without inputted themes
import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
import os

df = pd.read_csv("Dummy Data/varied_dummy_module_data.csv")
df['Combined_Text'] = df['Module_Syllabus'].fillna('') + ' ' + df['Module_Objectives'].fillna('')
df['Start_Year'] = df['Academic_year'].str.extract(r'(\d{4})')

output_base = "bertopic_outputs"
os.makedirs(output_base, exist_ok=True)

def run_bertopic_grouped(df, group_col):
    groups = df[group_col].dropna().unique()
    for group in groups:
        subset = df[df[group_col] == group]
        if len(subset) < 5:
            continue

        documents = subset['Combined_Text'].astype(str).tolist()
        timestamps = subset['Start_Year'].astype(str).tolist()

        vectorizer_model = CountVectorizer(stop_words="english")
        topic_model = BERTopic(vectorizer_model=vectorizer_model)
        topics, _ = topic_model.fit_transform(documents)
        topics_over_time = topic_model.topics_over_time(documents, timestamps)

        safe_name = group.replace(" ", "_").replace(",", "").replace("&", "and")
        group_dir = os.path.join(output_base, f"{group_col}_{safe_name}")
        os.makedirs(group_dir, exist_ok=True)

        topic_model.save(os.path.join(group_dir, "bertopic_model"))
        topic_model.visualize_topics_over_time(topics_over_time).write_html(
            os.path.join(group_dir, "topics_over_time.html")
        )
        print(f"Saved {group_col} '{group}' to: {group_dir}")

run_bertopic_grouped(df, "Module_Owner_Faculty")
run_bertopic_grouped(df, "Module_Owner_School")