"""Browser voice-typing enhancement for the Streamlit chat input."""
from __future__ import annotations

import streamlit.components.v1 as components


def inject_voice_input() -> None:
    """Add a microphone button immediately before Streamlit's send button.

    Uses the browser Web Speech API so speech is transcribed locally by the
    browser/OS speech service and inserted into the existing chat textarea.
    It never auto-submits the message.
    """
    components.html(
        """
        <script>
        (() => {
          const parent = window.parent.document;
          const install = () => {
            const root = parent.querySelector('[data-testid="stChatInput"]');
            if (!root || root.dataset.lexassistVoice === "1") return;
            const send = root.querySelector('button');
            const textarea = root.querySelector('textarea');
            if (!send || !textarea) return;

            root.dataset.lexassistVoice = "1";
            const button = parent.createElement("button");
            button.type = "button";
            button.className = "lexassist-voice-button";
            button.setAttribute("aria-label", "Voice input");
            button.title = "Voice input";
            button.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M5 11a7 7 0 0 0 14 0"></path><path d="M12 18v3"></path><path d="M9 21h6"></path></svg>';

            Object.assign(button.style, {
              width: "38px",
              height: "38px",
              minWidth: "38px",
              margin: "0 4px 0 0",
              border: "1px solid transparent",
              borderRadius: "10px",
              background: "transparent",
              color: "var(--muted, #94a3b8)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              flex: "0 0 auto"
            });

            const host = send.parentElement;
            if (!host) return;
            host.insertBefore(button, send);

            const Recognition = window.SpeechRecognition ||
              window.webkitSpeechRecognition;

            if (!Recognition) {
              button.disabled = true;
              button.title = "Voice input is not supported by this browser";
              button.style.opacity = "0.45";
              return;
            }

            let recognition = null;
            let listening = false;

            const setValue = (value) => {
              const setter = Object.getOwnPropertyDescriptor(
                HTMLTextAreaElement.prototype, "value"
              )?.set;
              if (setter) setter.call(textarea, value);
              else textarea.value = value;
              textarea.dispatchEvent(new Event("input", {bubbles: true}));
              textarea.dispatchEvent(new Event("change", {bubbles: true}));
              textarea.focus();
            };

            const setListening = (active) => {
              listening = active;
              button.style.background = active
                ? "rgba(239,68,68,.14)"
                : "transparent";
              button.style.color = active
                ? "#ef4444"
                : "var(--muted, #94a3b8)";
              button.innerHTML = active
                ? '<span aria-hidden="true">■</span>'
                : '<svg aria-hidden="true" viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M5 11a7 7 0 0 0 14 0"></path><path d="M12 18v3"></path><path d="M9 21h6"></path></svg>';
              button.title = active ? "Stop voice input" : "Voice input";
            };

            const start = () => {
              recognition = new Recognition();
              recognition.continuous = false;
              recognition.interimResults = false;
              recognition.lang = navigator.language || "en-IN";

              recognition.onresult = (event) => {
                const transcript = Array.from(event.results)
                  .map(r => r[0]?.transcript || "")
                  .join(" ")
                  .trim();
                if (!transcript) return;
                const current = textarea.value.trim();
                setValue(current ? current + " " + transcript : transcript);
              };

              recognition.onerror = () => setListening(false);
              recognition.onend = () => setListening(false);
              setListening(true);
              try { recognition.start(); }
              catch (_) { setListening(false); }
            };

            button.addEventListener("click", (event) => {
              event.preventDefault();
              event.stopPropagation();
              if (listening && recognition) {
                try { recognition.stop(); } catch (_) {}
                return;
              }
              start();
            });
          };

          install();
          const observer = new MutationObserver(install);
          observer.observe(parent.body, {childList: true, subtree: true});
          setTimeout(install, 250);
          setTimeout(install, 1000);
        })();
        </script>
        """,
        height=0,
    )
