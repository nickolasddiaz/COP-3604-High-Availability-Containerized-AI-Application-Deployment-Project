const messageform = document.getElementById('message-form');
const textarea = document.getElementById('message-input');
const chatcontainer = document.getElementById('chat-bot');

textarea.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        this.form.requestSubmit();
    }
});

chat_id = messageform.action;

messageform.addEventListener('submit', async (event) => {
    function put_new_message(message, person){
        const p = document.createElement("p");
        p.textContent = `${person}: ${message}`;
        chatcontainer.append(p);
    }

    event.preventDefault();

    put_new_message(textarea.value, "You")

    const response = await fetch(chat_id, {
        method: 'POST',
        body: new FormData(event.currentTarget)
    });

    if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
    }

    textarea.value = '';

    const data = await response.json();
    if ("chat_id" in data) {
        chat_id = `/send/${data["chat_id"]}`;
        chat_url = `/chat/${data["chat_id"]}`;

        window.history.replaceState({
            filter: 'active'
        }, '', chat_url);
    }

    put_new_message(data["message"], "Bot")
});