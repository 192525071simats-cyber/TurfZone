/**
 * Turf-Bot AI Assistant Interactive Chat Engine
 */

function formatMarkdown(text) {
  if (!text) return '';
  let formatted = text
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italics
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Links [text](url)
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" style="color: var(--accent-cyan); text-decoration: underline; font-weight: 600;">$1</a>')
    // Bullet points
    .replace(/^• (.*$)/gim, '<div style="margin-left: 0.5rem; margin-bottom: 0.25rem;">• $1</div>')
    // Line breaks
    .replace(/\n/g, '<br>');
  return formatted;
}

function appendMessage(sender, text, cards = []) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-msg ${sender}`;

  let cardsHtml = '';
  if (cards && cards.length > 0) {
    cardsHtml = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-top: 1rem;">
        ${cards.map(c => `
          <div class="card" style="padding: 0.75rem; background: var(--bg-card); font-size: 0.85rem;">
            <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 0.2rem;">${c.name}</div>
            <div style="color: var(--text-secondary); font-size: 0.75rem; margin-bottom: 0.4rem;">📍 ${c.location}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 800; color: #34d399;">₹${c.price_per_hour}/hr</span>
              <a href="/turf/${c.id}" class="btn btn-primary btn-sm" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;">View</a>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  if (sender === 'bot') {
    msgDiv.innerHTML = `
      <div class="chat-avatar" style="width: 34px; height: 34px; font-size: 1.1rem; flex-shrink: 0;">🤖</div>
      <div class="chat-bubble">
        ${formatMarkdown(text)}
        ${cardsHtml}
      </div>
    `;
  } else {
    msgDiv.innerHTML = `
      <div class="chat-bubble">${text}</div>
    `;
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-msg bot typing-indicator-msg';
  typingDiv.id = 'chat-typing-indicator';
  typingDiv.innerHTML = `
    <div class="chat-avatar" style="width: 34px; height: 34px; font-size: 1.1rem;">🤖</div>
    <div class="chat-bubble" style="color: var(--text-muted); font-style: italic;">
      Turf-Bot is analyzing facilities...
    </div>
  `;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
  const typingElem = document.getElementById('chat-typing-indicator');
  if (typingElem) typingElem.remove();
}

function updateQuickChips(chips) {
  const chipsContainer = document.getElementById('chat-chips-container');
  if (!chipsContainer || !chips) return;

  chipsContainer.innerHTML = chips.map(chip => `
    <button type="button" class="chip-btn" onclick="sendQuickMessage('${chip.replace(/'/g, "\\'")}')">${chip}</button>
  `).join('');
}

async function sendChatMessage(userText) {
  const input = document.getElementById('chat-user-input');
  const message = userText || (input ? input.value.trim() : '');
  if (!message) return;

  if (input) input.value = '';

  appendMessage('user', message);
  showTypingIndicator();

  const res = await API.post('/chatbot/message', { message });
  removeTypingIndicator();

  if (res.ok && res.data) {
    appendMessage('bot', res.data.reply, res.data.cards);
    if (res.data.quick_replies) {
      updateQuickChips(res.data.quick_replies);
    }
  } else {
    appendMessage('bot', '⚠️ Sorry, I encountered an issue connecting to the TurfZone assistant. Please try again.');
  }
}

function sendQuickMessage(text) {
  // Strip emojis from beginning if sending search query
  const cleanText = text.replace(/^[^\w\s]+/, '').trim();
  sendChatMessage(cleanText);
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('chat-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      sendChatMessage();
    });
  }

  // Send initial welcome message
  setTimeout(() => {
    sendChatMessage('Hello');
  }, 400);
});
