import { useState } from "react";
import { Bot, Send, MessageCircle, X } from "lucide-react";

export default function KrishiBotWidget() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hey there 👋 How can I help you today?",
    },
  ]);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = {
      role: "user",
      text: message,
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
            history: [],
          }),
        }
      );

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.reply || "No response",
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Unable to connect to KrishiBot.",
        },
      ]);
    }

    setMessage("");
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 w-16 h-16 rounded-full bg-red-600 text-white shadow-xl flex items-center justify-center z-50"
      >
        {open ? <X size={30} /> : <MessageCircle size={30} />}
      </button>

      {/* Chat Window */}
      {open && (
        <div className="fixed bottom-24 right-6 w-[370px] h-[550px] bg-white rounded-2xl shadow-2xl border overflow-hidden z-50 flex flex-col">

          {/* Header */}
          <div className="bg-red-700 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot />
              <h2 className="font-bold text-xl">
                KrishiBot
              </h2>
            </div>

            <button onClick={() => setOpen(false)}>
              <X />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50 space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${
                  msg.role === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                    msg.role === "user"
                      ? "bg-green-600 text-white"
                      : "bg-gray-200 text-black"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-4 border-t flex gap-2">
            <input
              type="text"
              placeholder="Type here..."
              value={message}
              onChange={(e) =>
                setMessage(e.target.value)
              }
              onKeyDown={(e) =>
                e.key === "Enter" &&
                sendMessage()
              }
              className="flex-1 border rounded-xl px-4 py-3 outline-none"
            />

            <button
              onClick={sendMessage}
              className="bg-green-600 text-white px-4 rounded-xl"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}