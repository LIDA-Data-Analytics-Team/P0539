
import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import os

parquet_path = "path_to/Module_NLP_data_clean.parquet"
df = pd.read_parquet(parquet_path)

df['Combined_Text'] = df['Module_Syllabus'].fillna('') + ' ' + df['Module_Objectives'].fillna('')
df['Start_Year'] = df['Academic_year'].str.extract(r'(\d{4})')

keywords_csv = "C:/pathto/CR_Keywords_clean.csv"
theme_keywords = pd.read_csv(keywords_csv)

seed_topic_list = []
custom_labels = []
theme_sentences = []
theme_names = []

for theme, values in theme_keywords.items():
    keywords = values.dropna().tolist()
    keywords = [kw.lower() for kw in keywords if isinstance(kw, str)]
    if keywords:
        seed_topic_list.append(keywords)
        custom_labels.append(theme)
        theme_names.append(theme)
        theme_sentences.append(f"{theme.lower()} concepts include: {', '.join(keywords)}")
        anchor_keywords = keywords[:5]
        anchor_variants = [
            f"{theme}: This module explores {', '.join(anchor_keywords[:3])} as key ideas.",
            f"{theme}: Students engage with topics like {', '.join(anchor_keywords[2:5])}.",
            f"{theme}: Learning includes {', '.join([anchor_keywords[0], anchor_keywords[-1], anchor_keywords[1]])}.",
            f"{theme}: The curriculum promotes {anchor_keywords[0]} and {anchor_keywords[2]} within {theme.lower()}.",
            f"{theme}: Modules cover {anchor_keywords[1]}, {anchor_keywords[3]}, and related ideas.",
            f"{theme}: {theme} teaching involves thinking critically about {anchor_keywords[0]}, {anchor_keywords[2]}, and {anchor_keywords[4]}."
        ]
        for sentence in anchor_variants:
            df = pd.concat([df, pd.DataFrame({
                "Combined_Text": [sentence],
                "Start_Year": ["0000"],
                "Module_Owner_Faculty": [f"Thematic_Anchor__{theme}"],
                "Module_Owner_School": [f"Thematic_Anchor__{theme}"]
            })], ignore_index=True)

output_base = "10_bertopic_thematic_v8_by_year_outputs"
os.makedirs(output_base, exist_ok=True)

def match_topic_to_theme(topic_words, model):
    topic_text = ' '.join(topic_words)
    topic_embedding = model.embedding_model.embed([topic_text])[0]
    theme_embeddings = model.embedding_model.embed(theme_sentences)
    sims = cosine_similarity([topic_embedding], theme_embeddings)[0]
    best_idx = sims.argmax()
    best_sim = sims[best_idx]
    return theme_names[best_idx] if best_sim >= 0.3 else "Unmatched"

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

        embedding_model = SentenceTransformer("path_to_sentence_transformer/all-miniLM-L6-v2")
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
            if not real_topics:
                print(f"  → No meaningful topics found for group '{group}'. Skipping.")
                continue

            os.makedirs(group_dir, exist_ok=True)
            topic_model.save(model_path)

            topic_assignments = []
            for idx, topic_id in enumerate(topics):
                if topic_id == -1:
                    continue
                words = [w for w, _ in topic_model.get_topic(topic_id)]
                matched_theme = match_topic_to_theme(words, topic_model)
                topic_assignments.append({
                    "Group": group,
                    "Group_Column": group_col,
                    "Topic_ID": topic_id,
                    "Matched_Theme": matched_theme,
                    "Top_Words": ', '.join(words),
                    "Start_Year": timestamps[idx]
                })

            df_match = pd.DataFrame(topic_assignments)
            df_match.to_csv(os.path.join(group_dir, "theme_match_detailed_v8.csv"), index=False)

        except Exception as e:
            print(f"  → Failed to process group '{group}': {e}")

if __name__ == "__main__":
    df['Faculty_Year'] = df['Module_Owner_Faculty'].astype(str) + "_" + df['Start_Year']
    run_bertopic_grouped(df, "Faculty_Year")
    df['School_Year'] = df['Module_Owner_School'].astype(str) + "_" + df['Start_Year']
    run_bertopic_grouped(df, "School_Year")
