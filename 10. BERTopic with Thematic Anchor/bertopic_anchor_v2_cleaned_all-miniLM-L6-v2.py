import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
import os

parquet_path = "/Module_NLP_data_clean.parquet"
df = pd.read_parquet(parquet_path)

if 'Module_Syllabus' in df.columns and 'Module_Objectives' in df.columns:
    df['Combined_Text'] = df['Module_Syllabus'].fillna('') + ' ' + df['Module_Objectives'].fillna('')
else:
    raise ValueError("Required columns 'Module_Syllabus' and 'Module_Objectives' not found in the data.")

if 'Academic_year' in df.columns:
    df['Start_Year'] = df['Academic_year'].str.extract(r'(\d{4})')
else:
    raise ValueError("Required column 'Academic_year' not found in the data.")

keywords_csv = "C:/Users/medlwha/Documents/NEW/CR_Keywords_clean.csv"
theme_keywords = pd.read_csv(keywords_csv)

seed_topic_list = []
custom_labels = []

for column in theme_keywords.columns:
    keywords = [kw.strip().lower() for kw in theme_keywords[column].dropna()]
    if keywords:
        seed_topic_list.append(keywords)
        custom_labels.append(column)

for label, words in zip(custom_labels, seed_topic_list):
    anchor_doc = f"{label.lower()} " + " ".join(words)
    df = pd.concat([df, pd.DataFrame({
        "Combined_Text": [anchor_doc],
        "Start_Year": ["0000"],
        "Module_Owner_Faculty": [f"Thematic_Anchor__{label}"],
        "Module_Owner_School": [f"Thematic_Anchor__{label}"]
    })], ignore_index=True)

output_base = "10_bertopic_thematic_v2_cleaned_outputs_all-miniLM-L6-v2"
os.makedirs(output_base, exist_ok=True)

def run_bertopic_grouped(df, group_col):
    groups = df[group_col].dropna().unique()

    for group in groups:
        subset = df[df[group_col] == group]
        if len(subset) < 5:
            continue

        documents = subset['Combined_Text'].astype(str).tolist()
        timestamps = subset['Start_Year'].astype(str).tolist()

        print(f"\nProcessing group: {group} ({len(documents)} docs)")

        embedding_model = SentenceTransformer("path_to/all-miniLM-L6-v2")
        umap_model = UMAP(n_neighbors=5, n_components=5, min_dist=0.0, metric='cosine')
        hdbscan_model = HDBSCAN(min_cluster_size=10, metric='euclidean', cluster_selection_method='eom')
        vectorizer_model = CountVectorizer(ngram_range=(1, 2), stop_words="english")

        topic_model = BERTopic(
            embedding_model=embedding_model,
            vectorizer_model=vectorizer_model,
            seed_topic_list=seed_topic_list,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            nr_topics="auto",
            calculate_probabilities=False,
            verbose=True
        )

        try:
            topics, _ = topic_model.fit_transform(documents)
            real_topics = set(topics) - {-1}
        except Exception as e:
            print(f"  → Failed to fit_transform for group '{group}': {e}")
            continue

        if real_topics:
            try:
                safe_name = group.replace(" ", "_").replace(",", "").replace("&", "and")
                group_dir = os.path.join(output_base, f"{group_col}_{safe_name}")
                os.makedirs(group_dir, exist_ok=True)

                topic_model.save(os.path.join(group_dir, "bertopic_model"))

                topics_over_time = topic_model.topics_over_time(documents, timestamps)
                filtered_topics = topics_over_time[topics_over_time['Frequency'] > 5]
                if not filtered_topics.empty:
                    fig = topic_model.visualize_topics_over_time(filtered_topics, top_n_topics=10)
                    fig.write_html(os.path.join(group_dir, "10_CR_topics_over_time.html"))
                else:
                    print(f"  → No frequent topics in topics_over_time for {group}")
            except Exception as e:
                print(f"  → Error during save/visualisation for group '{group}': {e}")
        else:
            print(f"  → No meaningful topics found for group '{group}'. Skipping model save and plot.")

if __name__ == "__main__":
    run_bertopic_grouped(df, "Module_Owner_Faculty")
    run_bertopic_grouped(df, "Module_Owner_School")
