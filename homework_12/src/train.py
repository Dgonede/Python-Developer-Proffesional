import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, Trainer, TrainingArguments

# Загрузка модели и токенизатора
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Установка токена для заполнения
tokenizer.pad_token = tokenizer.eos_token

model = GPT2LMHeadModel.from_pretrained(model_name)

# Загрузка данных
with open("data/data.txt", "r", encoding="utf-8") as file:
    dataset = file.read().strip()  # Читаем весь текст как одну строку

# Подготовка данных
train_encodings = tokenizer(dataset, truncation=True, padding=True, return_tensors="pt")

# Создание объекта Dataset
class CustomDataset(torch.utils.data.Dataset):
    def __init__(self, encodings):
        self.encodings = encodings

    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item['labels'] = item['input_ids']  # Устанавливаем labels равными input_ids
        return item

    def __len__(self):
        return len(self.encodings['input_ids'])

train_dataset = CustomDataset(train_encodings)

# Настройка параметров обучения
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=1,
    per_device_train_batch_size=1,
    save_steps=10_000,
    save_total_limit=2,
)

# Создание Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
)

# Запуск обучения
trainer.train()

# Сохранение модели
model.save_pretrained('./results')
tokenizer.save_pretrained('./results')