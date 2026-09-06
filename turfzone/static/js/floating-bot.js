/**
 * Global Floating Turf-Bot Assistant Launcher
 */

document.addEventListener('DOMContentLoaded', () => {
  // Don't render floating widget if already on the dedicated /turf-bot page
  if (window.location.pathname === '/turf-bot') return;

  // Create Widget Markup
  const widgetContainer = document.createElement('div');
  widgetContainer.id = 'floating-bot-widget';
  widgetContainer.innerHTML = `
    <!-- Floating Trigger Button -->
    <button id="floating-bot-btn" class="floating-bot-btn" aria-label="Open Turf-Bot">
      <span class="bot-icon">🤖</span>
      <span class="bot-badge">AI</span>
    </button>

    <!-- Floating Chat Window -->
    <div id="floating-chat-popup" class="floating-chat-popup">
      <div class="floating-chat-header">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
          <div class="chat-avatar" style="width: 32px; height: 32px; font-size: 1.1rem;">🤖</div>
          <div>
            <div style="font-weight: 700; font-size: 0.95rem; color: #fff;">Turf-Bot Assistant</div>
            <div style="font-size: 0.7rem; color: #34d399;">● Online & Ready</div>
          </div>
        </div>
        <button id="floating-chat-close" class="floating-chat-close" aria-label="Minimize Chat">&times;</button>
      </div>

      <div class="floating-chat-body" id="floating-chat-messages">
        <div class="chat-msg bot">
          <div class="chat-avatar" style="width: 28px; height: 28px; font-size: 0.95rem;">🤖</div>
          <div class="chat-bubble" style="font-size: 0.85rem;">
            👋 Hi! I can help you find venues, compare rates, or check tournaments in Chennai. What sport are you playing?
          </div>
        </div>
      </div>

      <div class="floating-chat-chips" id="floating-chat-chips">
        <button type="button" class="chip-btn" onclick="sendFloatingMsg('⚽ Football turfs')">⚽ Football</button>
        <button type="button" class="chip-btn" onclick="sendFloatingMsg('🏏 Cricket')">🏏 Cricket</button>
        <button type="button" class="chip-btn" onclick="sendFloatingMsg('💰 Cheapest turfs')">💰 Cheap</button>
        <button type="button" class="chip-btn" onclick="sendFloatingMsg('🏆 Tournaments')">🏆 Cups</button>
      </div>

      <form id="floating-chat-form" class="floating-chat-footer">
        <input type="text" id="floating-chat-input" class="form-control" placeholder="Ask Turf-Bot..." style="font-size: 0.85rem; padding: 0.5rem 0.75rem;" autocomplete="off" required>
        <button type="submit" class="btn btn-primary btn-sm" style="padding: 0.5rem 0.85rem;">➔</button>
      </form>
    </div>
  `;

  document.body.appendChild(widgetContainer);

  const btn = document.getElementById('floating-bot-btn');
  const popup = document.getElementById('floating-chat-popup');
  const closeBtn = document.getElementById('floating-chat-close');
  const form = document.getElementById('floating-chat-form');

  if (btn && popup) {
    btn.addEventListener('click', () => {
      popup.classList.toggle('active');
      if (popup.classList.contains('active')) {
        document.getElementById('floating-chat-input')?.focus();
      }
    });
  }

  if (closeBtn && popup) {
    closeBtn.addEventListener('click', () => {
      popup.classList.remove('active');
    });
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = document.getElementById('floating-chat-input');
      const msg = input.value.trim();
      if (!msg) return;
      input.value = '';
      sendFloatingMsg(msg);
    });
  }
});

function formatMarkdownPopup(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" style="color: var(--accent-cyan); text-decoration: underline;">$1</a>')
    .replace(/^• (.*$)/gim, '<div style="margin-left: 0.3rem;">• $1</div>')
    .replace(/\n/g, '<br>');
}

async function sendFloatingMsg(userMsg) {
  const container = document.getElementById('floating-chat-messages');
  if (!container) return;

  // Clean prompt
  const cleanMsg = userMsg.replace(/^[^\w\s]+/, '').trim();

  // User msg
  const userDiv = document.createElement('div');
  userDiv.className = 'chat-msg user';
  userDiv.innerHTML = `<div class="chat-bubble" style="font-size: 0.85rem;">${cleanMsg}</div>`;
  container.appendChild(userDiv);
  container.scrollTop = container.scrollHeight;

  // Typing
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-msg bot';
  typingDiv.id = 'floating-typing';
  typingDiv.innerHTML = `
    <div class="chat-avatar" style="width: 28px; height: 28px; font-size: 0.95rem;">🤖</div>
    <div class="chat-bubble" style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">Thinking...</div>
  `;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;

  const res = await API.post('/chatbot/message', { message: cleanMsg });
  document.getElementById('floating-typing')?.remove();

  if (res.ok && res.data) {
    const botDiv = document.createElement('div');
    botDiv.className = 'chat-msg bot';
    botDiv.innerHTML = `
      <div class="chat-avatar" style="width: 28px; height: 28px; font-size: 0.95rem;">🤖</div>
      <div class="chat-bubble" style="font-size: 0.85rem;">${formatMarkdownPopup(res.data.reply)}</div>
    `;
    container.appendChild(botDiv);
    container.scrollTop = container.scrollHeight;
  }
}
