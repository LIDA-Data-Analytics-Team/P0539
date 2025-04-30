
import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
import os

parquet_path = "path/Module_NLP_data_clean.parquet"
df = pd.read_parquet(parquet_path)

if 'Module_Syllabus' in df.columns and 'Module_Objectives' in df.columns:
    df['Combined_Text'] = df['Module_Syllabus'].fillna('') + ' ' + df['Module_Objectives'].fillna('')
else:
    raise ValueError("Required columns 'Module_Syllabus' and 'Module_Objectives' not found in the data.")

if 'Academic_year' in df.columns:
    df['Start_Year'] = df['Academic_year'].str.extract(r'(\d{4})')
else:
    raise ValueError("Required column 'Academic_year' not found in the data.")

keywords_csv = "CR_Keywords_clean.csv"
theme_keywords = pd.read_csv(keywords_csv)

seed_topic_list = []
custom_labels = []

for column in theme_keywords.columns:
    keywords = theme_keywords[column].dropna().tolist()
    if keywords: 
        seed_topic_list.append(keywords)
        custom_labels.append(column)

output_base = "bertopic_outputs_CR.v1"
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
        embedding_model = SentenceTransformer("pathto/all-MiniLM-L6-v2")

        topic_model = BERTopic(
            embedding_model=embedding_model,
            vectorizer_model=vectorizer_model,
            seed_topic_list=seed_topic_list,
            nr_topics="auto",
            calculate_probabilities=True,
            verbose=True
        )

        topics, _ = topic_model.fit_transform(documents)

        label_mapping = {i: custom_labels[i] for i in range(len(custom_labels))}
        topic_model.set_topic_labels(label_mapping)

        topics_over_time = topic_model.topics_over_time(documents, timestamps)

        filtered_topics = topics_over_time[topics_over_time['Frequency'] > 5]

        safe_name = group.replace(" ", "_").replace(",", "").replace("&", "and")
        group_dir = os.path.join(output_base, f"{group_col}_{safe_name}")
        os.makedirs(group_dir, exist_ok=True)

        topic_model.save(os.path.join(group_dir, "bertopic_model"))

        if not filtered_topics.empty:
            fig = topic_model.visualize_topics_over_time(filtered_topics, top_n_topics=10)
            fig.write_html(os.path.join(group_dir, "10_CR_topics_over_time.html"))

        print(f"Saved {group_col} '{group}' to: {group_dir}")

if __name__ == "__main__":
    run_bertopic_grouped(df, "Module_Owner_Faculty")
    run_bertopic_grouped(df, "Module_Owner_School")
