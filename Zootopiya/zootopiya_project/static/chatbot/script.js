$(document).ready(function() {
    console.log("Чат-бот загружен!");

    $("#chatbot-button").click(function() {
        $("#chatbot-window").toggle();
    });

    $("#close-chat").click(function() {
        $("#chatbot-window").hide();
    });

    $("#send-message").click(function() {
        sendMessage();
    });

    $("#chat-input").keypress(function(e) {
        if (e.which === 13) {  // Enter
            sendMessage();
        }
    });

    function sendMessage() {
        let userMessage = $("#chat-input").val().trim();
        if (userMessage === "") return;

        $("#chat-messages").append(`<div class="user-message">${userMessage}</div>`);
        $("#chat-input").val("");

        $.ajax({
            url: "/chatbot-response/",  // Используем актуальный URL
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ message: userMessage }),
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function(response) {
                $("#chat-messages").append(`<div class="bot-message">${response.response}</div>`);
            },
            error: function() {
                $("#chat-messages").append(`<div class="bot-message error">Ошибка сервера</div>`);
            }
        });
    }

    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }
});