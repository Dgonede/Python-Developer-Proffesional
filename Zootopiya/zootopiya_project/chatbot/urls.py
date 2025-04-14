from django.urls import path
from .views import chatbot_response, chat_view

urlpatterns = [
    path("chatbot/", chat_view, name="chat_view"),
    path("chatbot-response/", chatbot_response, name="chatbot_response"),  # API бота
]