import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import plotly.graph_objects as go
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

keywords_csv = "path/CR_Keywords_clean.csv"
theme_keywords = pd.read_csv(keywords_csv)

seed_topic_list = []
custom_labels = []
theme_sentences = []
theme_names = []

for theme, values in theme_keywords.items():
    keywords = values.dropna().tolist()[:5]
    if keywords:
        seed_topic_list.append([kw.lower() for kw in keywords])
        custom_labels.append(theme)
        theme_sentences.append(f"{theme.lower()} concepts include: {', '.join(keywords)}")
        theme_names.append(theme)
        anchor_variants = [
            f"{theme}: This module explores {', '.join(keywords[:3])} as key concepts.",
            f"{theme}: Students engage with topics like {', '.join(keywords[2:5])} in this theme.",
            f"{theme}: Learning activities include {', '.join([keywords[0], keywords[4], keywords[1]])}."
        ]
        for sentence in anchor_variants:
            df = pd.concat([df, pd.DataFrame({
                "Combined_Text": [sentence],
                "Start_Year": ["0000"],
                "Module_Owner_Faculty": [f"Thematic_Anchor__{theme}"],
                "Module_Owner_School": [f"Thematic_Anchor__{theme}"]
            })], ignore_index=True)

output_base = "10_bertopic_thematic_v7_cleaned_outputs_all-miniLM-L6-v2"
os.makedirs(output_base, exist_ok=True)

def match_topic_to_theme(topic_words, model):
    topic_text = ' '.join(topic_words)
    topic_embedding = model.embedding_model.embed([topic_text])[0]
    theme_embeddings = model.embedding_model.embed(theme_sentences)
    sims = cosine_similarity([topic_embedding], theme_embeddings)[0]
    best_idx = sims.argmax()
    best_sim = sims[best_idx]
    return theme_names[best_idx] if best_sim >= 0.3 else "Unmatched"

def generate_bar_chart_html(topic_freq_dict, model, output_path, title):
    items = sorted(topic_freq_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    labels, values = [], []
    for topic_id, freq in items:
        words = [w for w, _ in model.get_topic(topic_id)[:10]]
        theme = match_topic_to_theme(words, model)
        label = f"Topic {topic_id} – {theme}"
        labels.append(label)
        values.append(freq)
    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker=dict(color='indianred')
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Document Count",
        yaxis_title="Topic",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=120, r=40, t=60, b=40),
        height=500
    )
    fig.write_html(output_path)

def run_bertopic_grouped(df, group_col):
    groups = df[group_col].dropna().unique()
    for group in groups:
        subset = df[df[group_col] == group]
        if len(subset) < 5:
            continue
        safe_name = group.replace(" ", "_").replace(",", "").replace("&", "and")
        group_dir = os.path.join(output_base, f"{group_col}_{safe_name}")
        model_path = os.path.join(group_dir, "bertopic_model")
        if os.path.isdir(group_dir) and os.path.exists(model_path):
            print(f"→ Skipping {group} (already processed)")
            continue
        documents = subset['Combined_Text'].astype(str).tolist()
        timestamps = subset['Start_Year'].astype(str).tolist()
        print(f"\nProcessing group: {group} ({len(documents)} docs)")
        embedding_model = SentenceTransformer("C:/Users/medlwha/Documents/Python Packages/all-miniLM-L6-v2")
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
                os.makedirs(group_dir, exist_ok=True)
                topic_model.save(model_path)
                topics_over_time = topic_model.topics_over_time(documents, timestamps)
                filtered = topics_over_time[topics_over_time['Frequency'] > 5]
                if not filtered.empty:
                    fig_time = topic_model.visualize_topics_over_time(filtered, top_n_topics=10)
                    fig_time.write_html(os.path.join(group_dir, "10_CR_topics_over_time_v7.html"))
                counts = pd.Series(topics).value_counts().to_dict()
                generate_bar_chart_html(
                    counts,
                    topic_model,
                    os.path.join(group_dir, "10_CR_topic_frequencies_v7.html"),
                    title=f"Topic Frequencies – {group}"
                )
            except Exception as e:
                print(f"  → Error during saving/visualisation for group '{group}': {e}")
        else:
            print(f"  → No meaningful topics found for group '{group}'. Skipping.")

if __name__ == "__main__":
    run_bertopic_grouped(df, "Module_Owner_Faculty")
    run_bertopic_grouped(df, "Module_Owner_School")
