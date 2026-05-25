import { useEffect, useRef, useState } from "react";
import "../App.css";

import { useLanguage } from "../context/LanguageContext";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const SUGGESTIONS_EN = [
  "Best crops for black soil?",
  "How to treat aphids on wheat?",
  "NPK ratio for tomatoes?",
  "What is PM-KISAN scheme?",
  "Drip vs sprinkler irrigation?",
];

const SUGGESTIONS_HI = [
  "काली मिट्टी के लिए सबसे अच्छे फसल कौन-से हैं?",
  "गेहूं में माहू/एफिड्स (aphids) का इलाज कैसे करें?",
  "टमाटर के लिए NPK अनुपात क्या होना चाहिए?",
  "पीएम-किसान योजना क्या है?",
  "ड्रिप बनाम स्प्रिंकलर सिंचाई में क्या अंतर है?",
];

export default function KrishiBot() {
  const { lang } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text) {
    const userText = (text || input).trim();
    if (!userText || loading) return;

    setInput("");
    setLoading(true);

    const newMessages = [...messages, { role: "user", content: userText }];
    setMessages(newMessages);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userText,
          history: newMessages.slice(0, -1).map((message) => ({
            role: message.role,
            content: message.content,
          })),
        }),
      });

      if (!res.ok) {
        const detail = await readApiError(res);
        throw new Error(detail);
      }

      const data = await res.json();

      if (data.blocked) {
        setMessages([
          ...newMessages,
          { role: "assistant", content: data.reply, blocked: true },
        ]);
        return;
      }

      setMessages([
        ...newMessages,
        { role: "assistant", content: data.reply || "I could not generate a reply." },
      ]);
    } catch (err) {
      const message =
        err instanceof TypeError
          ? "Cannot connect to the FastAPI backend at http://localhost:8000."
          : err.message;

      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `Error: ${message}`,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <section className="kb-page">
      <div className="kb-root">
        <header className="kb-header">
          <div className="kb-logo" aria-hidden="true">
            KB
          </div>
          <div className="kb-heading">
            <h1 className="kb-title">KrishiBot</h1>
            <p className="kb-subtitle">by KrishiDrishti AI - Agricultural Intelligence</p>
          </div>
          <div className="kb-status">
            <span className="kb-dot" />
            Active
          </div>
        </header>

        <div className="kb-messages">
          {/* Suggestions should only show on empty chat; never stop permanently after questions */}
          {messages.length === 0 && (
            <div className="kb-msg bot">
              <div className="kb-avatar">AI</div>
              <div className="kb-bubble">
                <strong>{lang === "hi" ? "नमस्ते! KrishiBot में आपका स्वागत है।" : "Namaste! Welcome to KrishiBot."}</strong>
                <p>
                  {lang === "hi" ? (
                    <>
                      मैं <strong>KrishiDrishti AI</strong> का कृषि AI हूँ।
                      <br />
                      फसलों, मिट्टी, कीट, सिंचाई या सरकारी योजनाओं के बारे में पूछें।
                    </>
                  ) : (
                    <>
                      I am your agricultural AI by <strong>KrishiDrishti AI</strong>.
                      Ask me about crops, soil, pests, irrigation, or farming schemes.
                    </>
                  )}
                </p>
                <div className="kb-chips">
                  {(lang === "hi" ? SUGGESTIONS_HI : SUGGESTIONS_EN).map((suggestion) => (
                    <button
                      className="kb-chip"
                      key={suggestion}
                      onClick={() => sendMessage(suggestion)}
                      type="button"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div className={`kb-msg ${message.role === "user" ? "user" : "bot"}`} key={index}>
              <div className="kb-avatar">{message.role === "user" ? "You" : "AI"}</div>
              <div
                className={["kb-bubble", message.blocked ? "blocked" : "", message.error ? "error" : ""]
                  .filter(Boolean)
                  .join(" ")}
              >
                {message.content.split("\n").map((line, lineIndex) => (
                  <span key={lineIndex}>
                    {line}
                    <br />
                  </span>
                ))}
              </div>
            </div>
          ))}

          {loading && (
            <div className="kb-msg bot">
              <div className="kb-avatar">AI</div>
              <div className="kb-bubble compact">
                <div className="kb-typing" aria-label="KrishiBot is typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="kb-input-area">
          <textarea
            className="kb-textarea"
            disabled={loading}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={lang === "hi" ? "फसल, मिट्टी, कीट, सिंचाई के बारे में पूछें..." : "Ask about crops, soil, pests, irrigation..."}
            rows={1}
            value={input}
          />
          <button
            className="kb-send"
            disabled={loading || !input.trim()}
            onClick={() => sendMessage()}
            type="button"
          >
            Send
          </button>
        </div>
        <p className="kb-footer">KrishiDrishti AI - Answers agriculture questions only</p>
      </div>
    </section>
  );
}

async function readApiError(response) {
  const fallback = response.statusText || `Request failed with status ${response.status}`;

  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
    if (typeof data.error === "string") return data.error;
    return fallback;
  } catch {
    const text = await response.text();
    return text || fallback;
  }
}
