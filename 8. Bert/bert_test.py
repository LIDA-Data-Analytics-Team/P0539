import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

df = pd.read_csv("Dummy Data/varied_dummy_module_data.csv")
df['Combined_Text'] = df['Module_Syllabus'].fillna('') + ' ' + df['Module_Objectives'].fillna('')
df['Start_Year'] = df['Academic_year'].str.extract(r'(\d{4})')

documents = df['Combined_Text'].astype(str).tolist()
timestamps = df['Start_Year'].astype(str).tolist()

vectorizer_model = CountVectorizer(stop_words="english")
topic_model = BERTopic(vectorizer_model=vectorizer_model)

topics, probs = topic_model.fit_transform(documents)
topics_over_time = topic_model.topics_over_time(documents, timestamps)

topic_model.save("bertopic_model")
topic_model.visualize_topics_over_time(topics_over_time).write_html("topics_over_time.html")
print("Done! Check topics_over_time.html")