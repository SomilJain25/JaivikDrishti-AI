import { useEffect, useRef, useState } from "react";
import "../App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const PIPELINE_STEPS = [
  { id: "input", label: "Question" },
  { id: "filter", label: "Topic filter" },
  { id: "context", label: "Context builder" },
  { id: "llm", label: "ChatGPT" },
  { id: "answer", label: "Answer" },
];

const SUGGESTIONS = [
  "Best crops for black soil?",
  "How to treat aphids on wheat?",
  "NPK ratio for tomatoes?",
  "What is PM-KISAN scheme?",
  "Drip vs sprinkler irrigation?",
];

export default function KrishiBot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(null);
  const [pipelineBlocked, setPipelineBlocked] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text) {
    const userText = (text || input).trim();
    if (!userText || loading) return;

    setInput("");
    setLoading(true);
    setPipelineBlocked(false);

    const newMessages = [...messages, { role: "user", content: userText }];
    setMessages(newMessages);

    setActiveStep("input");
    await delay(300);
    setActiveStep("filter");
    await delay(400);

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
        let detail = "Server error";
        try {
          const err = await res.json();
          detail = err.detail || err.error || detail;
        } catch {
          detail = await res.text();
        }
        throw new Error(detail);
      }

      const data = await res.json();

      if (data.blocked) {
        setPipelineBlocked(true);
        setActiveStep("filter");
        setMessages([
          ...newMessages,
          { role: "assistant", content: data.reply, blocked: true },
        ]);
        await delay(1500);
        setActiveStep(null);
        setPipelineBlocked(false);
        return;
      }

      setActiveStep("context");
      await delay(400);
      setActiveStep("llm");

      setMessages([
        ...newMessages,
        { role: "assistant", content: data.reply || "I could not generate a reply." },
      ]);

      setActiveStep("answer");
      await delay(1200);
      setActiveStep(null);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `Error: ${err.message}. Make sure the FastAPI backend is running on port 8000.`,
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

        <div className="kb-pipeline" aria-label="KrishiBot response pipeline">
          {PIPELINE_STEPS.map((step, index) => (
            <span className="kb-pipeline-item" key={step.id}>
              <span
                className={[
                  "kb-step",
                  activeStep === step.id ? (pipelineBlocked ? "blocked" : "active") : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <span className="kb-step-dot" />
                {step.label}
              </span>
              {index < PIPELINE_STEPS.length - 1 && <span className="kb-sep">/</span>}
            </span>
          ))}
        </div>

        <div className="kb-messages">
          {messages.length === 0 && (
            <div className="kb-msg bot">
              <div className="kb-avatar">AI</div>
              <div className="kb-bubble">
                <strong>Namaste! Welcome to KrishiBot.</strong>
                <p>
                  I am your agricultural AI by <strong>KrishiDrishti AI</strong>.
                  Ask me about crops, soil, pests, irrigation, or farming schemes.
                </p>
                <div className="kb-chips">
                  {SUGGESTIONS.map((suggestion) => (
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
            placeholder="Ask about crops, soil, pests, irrigation..."
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

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
