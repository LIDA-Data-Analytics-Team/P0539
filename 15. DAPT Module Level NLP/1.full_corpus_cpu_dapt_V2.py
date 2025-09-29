from transformers import AutoTokenizer, AutoModelForMaskedLM, DataCollatorForLanguageModeling, Trainer, TrainingArguments
from datasets import load_dataset
from tqdm.auto import tqdm

base_model = r"all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(base_model)

dataset = load_dataset("text", data_files={"train": r"\curriculum_corpus.txt"})

def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=256)

for _ in tqdm(range(1), desc="Tokenizing dataset"):
    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=["text"])

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=True, mlm_probability=0.1)

model = AutoModelForMaskedLM.from_pretrained(base_model)

training_args = TrainingArguments(
    output_dir=r"C:/Users/medlwha/Documents/MODULE_LEVEL_NLP/DAPT/domain_adapted_model_v2",
    overwrite_output_dir=True,
    num_train_epochs=3,
    per_device_train_batch_size=8,
    save_steps=500,
    save_total_limit=1,
    logging_steps=200,
    warmup_steps=100,
    learning_rate=2e-5,
    weight_decay=0.01,
    no_cuda=True
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    data_collator=data_collator,
)

print("Starting training...")
trainer.train()
print("Training complete. Saving model...")

trainer.save_model("./domain_adapted_model")
tokenizer.save_pretrained("./domain_adapted_model")
print("Model saved in ./domain_adapted_model")
