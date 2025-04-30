import pandas as pd
import numpy as np
import os
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

models_base_path = "path to/bertopic_outputs_CR.v4"
keywords_csv_path = "path to/CR_Keywords_clean.csv"
local_model_path = "path to/all-miniLM-L6-v2"
output_report_path = "bertopic_theme_matches_report_bert.csv"

embedder = SentenceTransformer(local_model_path)

theme_keywords = pd.read_csv(keywords_csv_path)
theme_sentences = []
theme_names = []
for column in theme_keywords.columns:
    keywords = theme_keywords[column].dropna().tolist()
    if keywords:
        combined = ' '.join(keywords)
        theme_sentences.append(combined)
        theme_names.append(column)

theme_embeddings = embedder.encode(theme_sentences, show_progress_bar=False)

def match_topic_to_theme(topic_words):
    topic_text = ' '.join(topic_words)
    topic_embedding = embedder.encode([topic_text], show_progress_bar=False)[0]
    sims = cosine_similarity([topic_embedding], theme_embeddings)[0]
    best_idx = np.argmax(sims)
    return theme_names[best_idx], round(sims[best_idx], 3)

all_matches = []


for group_folder in os.listdir(models_base_path):
    model_path = os.path.join(models_base_path, group_folder, "bertopic_model")
    if os.path.exists(model_path):
        try:
            model = BERTopic.load(model_path)
            topics_info = model.get_topic_info()


            for _, row in topics_info.iterrows():
                if row['Topic'] == -1:
                    continue
                topic_words = row['Name'].split('_')
                best_theme, similarity = match_topic_to_theme(topic_words)
                total_frequency = row['Count']


                match_entry = {
                    "Faculty_Group": group_folder,
                    "Topic_ID": row['Topic'],
                    "Top_Words": row['Name'],
                    "Best_Matched_Theme": best_theme,
                    "Total_Frequency": total_frequency,
                    "Similarity": similarity
                }
                all_matches.append(match_entry)

        except Exception as e:
            print(f"Failed to load model at {model_path}: {e}")

matches_df = pd.DataFrame(all_matches)
matches_df.to_csv(output_report_path, index=False)
print(f"Saved BERT-based matching report to {output_report_path}")
