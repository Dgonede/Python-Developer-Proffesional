import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Загрузка дообученной модели и токенизатора
model = GPT2LMHeadModel.from_pretrained('./results')
tokenizer = GPT2Tokenizer.from_pretrained('./results')

def generate_response(prompt):
    inputs = tokenizer.encode(prompt, return_tensors='pt')
    attention_mask = torch.ones(inputs.shape, dtype=torch.long)  # Создаем маску внимания
    outputs = model.generate(inputs, attention_mask=attention_mask, max_length=50, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Пример использования
if __name__ == "__main__":
    while True:
        user_input = input("Вы: ")
        if user_input.lower() in ["выход", "exit"]:
            break
        response = generate_response(user_input)
        print("Бот:", response)