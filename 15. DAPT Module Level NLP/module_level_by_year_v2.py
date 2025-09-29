import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import os

def run_module_level_theme_similarity_by_year(
    module_parquet_path= r"C:\Users\medlwha\Documents\MODULE_LEVEL_NLP\Module_NLP_data_clean.parquet",
    theme_keywords_csv= r"C:\Users\medlwha\Documents\MODULE_LEVEL_NLP\CR_Keywords_clean.csv",
    model_path= r"C:\Users\medlwha\Documents\MODULE_LEVEL_NLP\DAPT\domain_adapted_sentence_model_v2",
    output_dir= r"C:\Users\medlwha\Documents\MODULE_LEVEL_NLP\DAPT\module_theme_similarity_matrix_v2"
):
    df = pd.read_parquet(module_parquet_path)
    df['Combined_Text'] = df['Module_Syllabus'].fillna('') + ' ' + df['Module_Objectives'].fillna('')
    theme_keywords = pd.read_csv(theme_keywords_csv)
    theme_names = list(theme_keywords.columns)
    theme_sentences = []
    for theme in theme_names:
        keywords = theme_keywords[theme].dropna().tolist()
        keywords = [kw.lower() for kw in keywords if isinstance(kw, str)]
        if keywords:
            theme_sentences.append(f"{theme.lower()} concepts include: {', '.join(keywords)}")
        else:
            theme_sentences.append(f"This theme is about {theme.lower()}.")
    embedding_model = SentenceTransformer(model_path)
    theme_embeddings = embedding_model.encode(theme_sentences)
    similarity_rows = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing modules"):
        module_code = row.get("Module_Code", f"Module_{idx}")
        module_title = row.get("Module_Title", "")
        module_faculty = row.get("Module_Owner_Faculty", "")
        module_school = row.get("Module_Owner_School", "")
        academic_year = row.get("Academic_year", "Unknown_Year")
        module_text = row['Combined_Text']
        module_embedding = embedding_model.encode([module_text])[0]
        sims = cosine_similarity([module_embedding], theme_embeddings)[0]
        row_data = {
            "Academic_year": academic_year,
            "Module_Code": module_code,
            "Module_Title": module_title,
            "Module_Faculty": module_faculty,
            "Module_School": module_school
        }
        for theme, score in zip(theme_names, sims):
            row_data[theme] = round(float(score), 4)
        similarity_rows.append(row_data)
    similarity_df = pd.DataFrame(similarity_rows)
    os.makedirs(output_dir, exist_ok=True)
    for year, group_df in similarity_df.groupby("Academic_year"):
        year_str = str(year).replace("/", "-")
        output_path = os.path.join(output_dir, f"module_theme_similarity_{year_str}.csv")
        group_df.to_csv(output_path, index=False)
        print(f"Saved: {output_path}")
    print(f"All yearly similarity matrices saved in {output_dir}")

if __name__ == "__main__":
    run_module_level_theme_similarity_by_year()
