import pandas as pd
import numpy as np
import os
from bertopic import BERTopic
from sklearn.metrics.pairwise import cosine_similarity

models_base_path = "path to/10_bertopic_thematic_v2_cleaned_outputs_all-miniLM-L6-v2"
keywords_csv_path = "C:/Users/medlwha/Documents/NEW/CR_Keywords_clean.csv"
output_report_path = "bertopic_theme_matches_v2.2.csv"

theme_keywords = pd.read_csv(keywords_csv_path)
theme_sentences = []
theme_names = []
for column in theme_keywords.columns:
    keywords = theme_keywords[column].dropna().tolist()
    if keywords:
        combined = ' '.join(keywords)
        theme_sentences.append(combined)
        theme_names.append(column)

def match_topic_to_theme(topic_words, model, theme_sentences, theme_names, min_sim=0.5):
    topic_text = ' '.join(topic_words)
    topic_embedding = model.embedding_model.embed([topic_text])[0]
    theme_embeddings = model.embedding_model.embed(theme_sentences)
    sims = cosine_similarity([topic_embedding], theme_embeddings)[0]
    best_idx = np.argmax(sims)
    best_sim = sims[best_idx]
    if best_sim < min_sim:
        return "Unmatched", round(best_sim, 3)
    return theme_names[best_idx], round(best_sim, 3)

all_matches = []

for group_folder in os.listdir(models_base_path):
    if "Thematic_Anchor__" in group_folder:
        continue

    model_path = os.path.join(models_base_path, group_folder, "bertopic_model")
    if os.path.exists(model_path):
        try:
            model = BERTopic.load(model_path)

            topics_info = model.get_topic_info()

            for _, row in topics_info.iterrows():
                if row['Topic'] == -1:
                    continue
                topic_id = row['Topic']
                topic_words = [word for word, _ in model.get_topic(topic_id)[:20]]
                best_theme, similarity = match_topic_to_theme(topic_words, model, theme_sentences, theme_names)
                total_frequency = row['Count']

                match_entry = {
                    "Faculty_Group": group_folder,
                    "Topic_ID": topic_id,
                    "Top_20_Words": ', '.join(topic_words),
                    "Best_Matched_Theme": best_theme,
                    "Total_Frequency": total_frequency,
                    "Similarity": similarity
                }
                all_matches.append(match_entry)

        except Exception as e:
            print(f"Failed to load model at {model_path}: {e}")

matches_df = pd.DataFrame(all_matches)
matches_df.to_csv(output_report_path, index=False)
print(f"Saved theme matching report to {output_report_path}")