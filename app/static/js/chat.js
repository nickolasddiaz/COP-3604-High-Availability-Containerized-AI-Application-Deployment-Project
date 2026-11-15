const messageform = document.getElementById('message-form');
const textarea = document.getElementById('message-input');
const chatcontainer = document.getElementById('chat-bot');
const chat_history_container = document.getElementById('chat-history-box');

const dropZone = document.getElementById('message-form');
const fileList = document.getElementById('file-list');
const attachments = document.getElementById('attachments'); // <input> multiple files
const attachmentFiles = new DataTransfer();
for (const file of attachments.files) {
    attachmentFiles.items.add(file);
}


// handle submitting the chat message form
enabled = true;

textarea.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        if (enabled)
            this.form.requestSubmit();
    }
});

chat_id = messageform.action;

function put_new_message(message, person, files) {
    const div = document.createElement("div");
    chatcontainer.append(div);

    const p1 = document.createElement("p");
    p1.innerHTML = `<b style="display: inline;">${person}: </b> ${files}`
    div.append(p1)
    const p2 = document.createElement("p");
    p2.innerHTML = message;
    div.append(p2)
}

function add_item_to_history(chat_id, chat_title) {
    const a = document.createElement("a");
    a.href = `/chat/${chat_id}`;
    a.innerHTML = `
        <li>${chat_title}</li>
        <button type="button" onclick="event.preventDefault(); event.stopPropagation(); download_chat('${chat_id}', '${chat_title}');">&#8681;</button>
    `;
    chat_history_container.prepend(a);
}

messageform.addEventListener('submit', async (event) => {
    try {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        enabled = false;
        textarea.disabled = true;

        const fileNames = Array.from(attachmentFiles.files).map(file => file.name);
        put_new_message(textarea.value, "User", fileNames)

        const response = await fetch(chat_id, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        if ("chat_id" in data) {
            chat_id = `/send/${data["chat_id"]}`;
            chat_url = `/chat/${data["chat_id"]}`;

            window.history.replaceState({
                filter: 'active'
            }, '', chat_url);

            add_item_to_history(data["chat_id"], data["chat_name"]);
        }

        put_new_message(data["message"], "System", []);

        textarea.value = '';
        fileList.replaceChildren();
        attachmentFiles.items.clear();

    } catch (error) {
        console.error("Something went wrong:", error.message);
        alert(`Something went wrong: ${error.message}`);
    } finally {
        enabled = true;
        textarea.disabled = false;
    }
});

// handle drag and dropping files

// prevent file from opening in a new tab
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
    });
});

// trigger when hovering over
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.add('highlight');
    });
});

// removing trigger when not hovering over
['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.remove('highlight');
    });
});

// dropped file list
dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    handleFiles(files);
});

function handleFiles(files) {
    for (const file of files) {
        const file_container = document.createElement('div');
        file_container.className = 'file_container';
        fileList.appendChild(file_container);

        const file_name = document.createElement('p');
        file_name.textContent = file.name;
        file_container.appendChild(file_name);

        const file_size = document.createElement('p');
        file_size.textContent = `${Math.round(file.size / 1024)} KB`;
        file_container.appendChild(file_size);

        const img = document.createElement("img");
        img.src = "/file.svg";
        img.alt = file.name;
        img.draggable = false
        file_container.appendChild(img);

        attachmentFiles.items.add(file);
        attachments.files = attachmentFiles.files;

        const button = document.createElement('button');
        button.innerHTML = '&#x2715;'; // X mark icon
        // delete it's container and remove the attachment
        button.onclick = (event) => {
            event.preventDefault();
            event.stopPropagation();
            const index = Array.from(attachmentFiles.files).findIndex(attachment => attachment === file);
            if (index !== -1) {
                attachmentFiles.items.remove(index);
                attachments.files = attachmentFiles.files;
            }
            file_container.remove();
        }

        file_container.appendChild(button);
    }
}