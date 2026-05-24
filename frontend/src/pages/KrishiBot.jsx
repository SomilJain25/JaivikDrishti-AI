// ============================================================
// KRISHIBOT FRONTEND — src/App.jsx
// React chat UI — calls FastAPI backend at localhost:8000
// ============================================================

import { useState, useRef, useEffect } from "react";
import "../App.css";

// ============================================================
// FastAPI runs on port 8000 by default (not 3001 like Express)
// ============================================================
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const PIPELINE_STEPS = [
  { id: "input",   label: "Question" },
  { id: "filter",  label: "Topic filter" },
  { id: "context", label: "Context builder" },
  { id: "llm",     label: "ChatGPT" },
  { id: "answer",  label: "Answer" },
];

const SUGGESTIONS = [
  "Best crops for black soil?",
  "How to treat aphids on wheat?",
  "NPK ratio for tomatoes?",
  "What is PM-KISAN scheme?",
  "Drip vs sprinkler irrigation?",
];

export default function App() {
  const [messages, setMessages]               = useState([]);
  const [input, setInput]                     = useState("");
  const [loading, setLoading]                 = useState(false);
  const [activeStep, setActiveStep]           = useState(null);
  const [pipelineBlocked, setPipelineBlocked] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ============================================================
  // Send message → FastAPI POST /chat
  // ============================================================
  async function sendMessage(text) {
    const userText = (text || input).trim();
    if (!userText || loading) return;

    setInput("");
    setLoading(true);
    setPipelineBlocked(false);

    const newMessages = [...messages, { role: "user", content: userText }];
    setMessages(newMessages);

    // Animate pipeline
    setActiveStep("input");
    await delay(300);
    setActiveStep("filter");
    await delay(400);

    try {
      // Call FastAPI backend
      // FastAPI expects: { message: string, history: [{role, content}] }
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userText,
          history: newMessages.slice(0, -1).map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      // Handle HTTP errors from FastAPI (422 validation, 500 server, etc.)
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Server error");
      }

      // FastAPI returns: { blocked, pipeline_step, reply }
      const data = await res.json();

      // Topic filter blocked the question
      if (data.blocked) {
        setPipelineBlocked(true);
        setActiveStep("filter");
        setMessages([...newMessages, { role: "assistant", content: data.reply, blocked: true }]);
        await delay(1500);
        setActiveStep(null);
        setPipelineBlocked(false);
        return;
      }

      // Animate remaining pipeline steps
      setActiveStep("context");
      await delay(400);
      setActiveStep("llm");

      setMessages([...newMessages, { role: "assistant", content: data.reply }]);

      setActiveStep("answer");
      await delay(1200);
      setActiveStep(null);

    } catch (err) {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `⚠️ Error: ${err.message}. Make sure FastAPI backend is running on port 8000.`,
          error: true,
        },
      ]);
      setActiveStep(null);
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
    <div className="kb-root">

      {/* Header */}
      <header className="kb-header">
        <div className="kb-logo">🌾</div>
        <div>
          <div className="kb-title">KrishiBot</div>
          <div className="kb-subtitle">by KrishiDrishti AI · Agricultural Intelligence</div>
        </div>
        <div className="kb-status">
          <span className="kb-dot" />
          Active
        </div>
      </header>

      {/* Pipeline Step Bar */}
      <div className="kb-pipeline">
        {PIPELINE_STEPS.map((step, i) => (
          <span key={step.id}>
            <span className={[
              "kb-step",
              activeStep === step.id ? (pipelineBlocked ? "blocked" : "active") : "",
            ].join(" ")}>
              <span className="kb-step-dot" />
              {step.label}
            </span>
            {i < PIPELINE_STEPS.length - 1 && <span className="kb-sep">›</span>}
          </span>
        ))}
      </div>

      {/* Messages */}
      <div className="kb-messages">

        {/* Welcome */}
        {messages.length === 0 && (
          <div className="kb-msg bot">
            <div className="kb-avatar">🌱</div>
            <div className="kb-bubble">
              <strong>नमस्ते! Welcome to KrishiBot 🌾</strong>
              <p>
                I'm your agricultural AI by <strong>KrishiDrishti AI</strong>.
                Ask me about crops, soil, pests, irrigation, or farming schemes.
              </p>
              <div className="kb-chips">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="kb-chip" onClick={() => sendMessage(s)}>{s}</button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Chat messages */}
        {messages.map((msg, i) => (
          <div key={i} className={`kb-msg ${msg.role === "user" ? "user" : "bot"}`}>
            <div className="kb-avatar">
              {msg.role === "user" ? "You" : "🌱"}
            </div>
            <div className={["kb-bubble", msg.blocked ? "blocked" : "", msg.error ? "error" : ""].join(" ")}>
              {msg.content.split("\n").map((line, j) => (
                <span key={j}>{line}<br /></span>
              ))}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="kb-msg bot">
            <div className="kb-avatar">🌱</div>
            <div className="kb-bubble">
              <div className="kb-typing">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="kb-input-area">
        <textarea
          className="kb-textarea"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about crops, soil, pests, irrigation..."
          rows={1}
          disabled={loading}
        />
        <button
          className="kb-send"
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          ➤
        </button>
      </div>
      <p className="kb-footer">KrishiDrishti AI · Answers agriculture questions only</p>
    </div>
  );
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}