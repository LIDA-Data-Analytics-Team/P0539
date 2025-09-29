from sentence_transformers import SentenceTransformer, models

mlm_model_path = "/MODULE_LEVEL_NLP/DAPT/domain_adapted_model"
word_embedding_model = models.Transformer(mlm_model_path)
pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension(), pooling_mode_mean_tokens=True)
sentence_model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
sentence_model.save("/DAPT/domain_adapted_sentence_model_v2")
