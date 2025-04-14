from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
import json
from .models import QuestionAnswer
from django.shortcuts import render
import os

UNKNOWN_QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "unknown_questions.txt")

# Стандартные вопросы и ответы
STANDARD_RESPONSES = {
    "привет": "Привет! Как я могу вам помочь?",
    "как дела?": "У меня все хорошо, спасибо! Чем могу помочь?",
    "что ты можешь?": "Я могу ответить на вопросы о нашем сайте и помочь вам с заказами.",
    "пока": "До свидания! Если возникнут вопросы, возвращайтесь.",
}

def chat_view(request):
    return render(request, "chatbot/chat.html")

@csrf_protect
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Получаем JSON из запроса
            user_message = data.get("message", "").strip().lower()  # Берем сообщение пользователя

            # Проверяем, есть ли ответ на стандартный вопрос
            if user_message in STANDARD_RESPONSES:
                bot_response = STANDARD_RESPONSES[user_message]
            else:
                # Поиск вопроса в базе данных
                try:
                    bot_response = QuestionAnswer.objects.get(question__iexact=user_message).answer
                except QuestionAnswer.DoesNotExist:
                    bot_response = "Извините, но у меня пока нет информации по данному вопросу."
                    # Если вопрос не найден, можно записать его в файл для дальнейшей обработки
                    with open(UNKNOWN_QUESTIONS_FILE, "a", encoding="utf-8") as file:
                        file.write(user_message + "\n")

            return JsonResponse({"response": bot_response})  # Отправляем ответ в JSON-формате

        except Exception as e:
            return JsonResponse({"response": "Ошибка обработки запроса."}, status=500)
    
    return JsonResponse({"response": "Неверный метод запроса."}, status=400)
