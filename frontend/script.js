document.addEventListener('DOMContentLoaded', () => {
  // Select DOM elements
  const chatWindow = document.getElementById('chat-window');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const chatForm = document.getElementById('chat-form');

  /**
   * Appends a message bubble to the chat window and auto-scrolls to the bottom.
   * Applies the error style if the message is from the bot and starts with "Error:".
   *
   * @param {string} text - Message text content
   * @param {boolean} isUser - True for user message, false for bot message
   */
  function addMessage(text, isUser) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');

    if (isUser) {
      messageElement.classList.add('user-message');
    } else {
      messageElement.classList.add('bot-message');
      // Apply error styling for bot messages starting with "Error:"
      if (typeof text === 'string' && text.startsWith('Error:')) {
        messageElement.classList.add('error-message');
      }
    }

    messageElement.textContent = text;
    chatWindow.appendChild(messageElement);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  /**
   * Displays the typing indicator bubble with 3 animated dots.
   */
  function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.classList.add('message', 'bot-message', 'typing-indicator');
    indicator.setAttribute('aria-label', 'Bot is typing');

    // Create 3 animated dots
    for (let i = 0; i < 3; i++) {
      const dot = document.createElement('span');
      dot.classList.add('dot');
      indicator.appendChild(dot);
    }

    chatWindow.appendChild(indicator);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  /**
   * Removes the typing indicator bubble from the chat window.
   */
  function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
      indicator.remove();
    }
  }

  /**
   * Handles sending the user message to the backend and rendering the bot's reply.
   */
  async function handleSend() {
    const messageText = userInput.value.trim();

    // Ignore empty or whitespace-only messages
    if (!messageText) return;

    // Display user message in chat
    addMessage(messageText, true);

    // Clear the input field
    userInput.value = '';

    // Show typing indicator and disable input and send button while waiting
    showTypingIndicator();
    userInput.disabled = true;
    sendBtn.disabled = true;

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageText }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      if (typeof data.reply !== 'string') {
        throw new Error('Invalid reply format');
      }

      // Remove typing indicator and render bot reply
      removeTypingIndicator();
      addMessage(data.reply, false);
    } catch (error) {
      // Remove typing indicator and display error message
      removeTypingIndicator();
      addMessage('Error: could not reach backend', false);
    } finally {
      // Re-enable input and send button, and refocus the input
      userInput.disabled = false;
      sendBtn.disabled = false;
      userInput.focus();
    }
  }

  // Handle message sending via form submit (covers Enter key and Send button click)
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSend();
  });

  // Display initial welcome message on page load
  addMessage(
    "Hi! I can answer questions about Heng Bunyi's resume. Try asking about skills, education, or experience.",
    false
  );
});
