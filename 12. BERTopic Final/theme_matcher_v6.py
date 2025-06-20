
import pandas as pd
import numpy as np
import os
import re
from bertopic import BERTopic
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

models_base_path = "10_bertopic_thematic_v8_by_year_outputs"
keywords_csv_path = "path to/CR_Keywords_clean.csv"
output_report_path = "path_to/bertopic_theme_matches_v6_year.csv"
embedding_model_path = r"path_to\all-MiniLM-L6-v2"

theme_keywords = pd.read_csv(keywords_csv_path)
embedding_model = SentenceTransformer(embedding_model_path)

theme_sentences = []
theme_names = []

for column in theme_keywords.columns:
    keywords = theme_keywords[column].dropna().tolist()[:5]
    if keywords:
        combined = f"{column.lower()} concepts include: " + ', '.join(keywords)
        theme_sentences.append(combined)
        theme_names.append(column)

theme_embeddings = embedding_model.encode(theme_sentences)

def match_topic_to_theme(topic_words):
    topic_text = ' '.join(topic_words)
    topic_embedding = embedding_model.encode([topic_text])[0]
    sims = cosine_similarity([topic_embedding], theme_embeddings)[0]
    best_idx = np.argmax(sims)
    best_sim = sims[best_idx]
    if best_sim < 0.3:
        return "Unmatched", round(best_sim, 3)
    return theme_names[best_idx], round(best_sim, 3)

all_matches = []

for group_folder in os.listdir(models_base_path):
    if "Thematic_Anchor__" in group_folder:
        continue

    model_path = os.path.join(models_base_path, group_folder, "bertopic_model")

    year_match_obj = re.search(r'(\d{4})', group_folder)
    year = year_match_obj.group(1) if year_match_obj else "Unknown"

    if os.path.exists(model_path):
        try:
            model = BERTopic.load(model_path)
            topics_info = model.get_topic_info()

            for _, row in topics_info.iterrows():
                if row['Topic'] == -1:
                    continue

                topic_id = row['Topic']
                topic_words = [word for word, _ in model.get_topic(topic_id)[:20]]
                best_theme, similarity = match_topic_to_theme(topic_words)
                total_frequency = row['Count']

                match_entry = {
                    "Faculty_Group": group_folder,
                    "Topic_ID": topic_id,
                    "Top_20_Words": ', '.join(topic_words),
                    "Best_Matched_Theme": best_theme,
                    "Total_Frequency": total_frequency,
                    "Similarity": similarity,
                    "Year": year
                }
                all_matches.append(match_entry)

        except Exception as e:
            print(f"Failed to load model at {model_path}: {e}")

matches_df = pd.DataFrame(all_matches)
try:
    matches_df.to_csv(output_report_path, index=False)
    print(f"Saved theme matching report to: {output_report_path}")
except Exception as e:
    fallback_path = os.path.expanduser("path_to_save/bertopic_theme_matches_v6_year_BACKUP.csv")
    matches_df.to_csv(fallback_path, index=False)
    print(f"Primary save failed. Backup saved to: {fallback_path}")
