"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Database, AlertTriangle, Code2, Trash2 } from "lucide-react";
import { chatApi } from "@/services/chatApi";
import { ChatMessage } from "@/types/chat";
import { Card } from "@/app/components/shared/Card";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    // Auto-scroll anchor
    const messagesEndRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg: ChatMessage = {
            id: Date.now().toString(),
            role: "user",
            content: input.trim(),
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        try {
            const aiResponse = await chatApi.sendMessage(userMsg.content);

            const aiMsg: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: aiResponse.explanation,
                sql_executed: aiResponse.generated_sql,
                execution_time_ms: aiResponse.execution_time_ms,
                results_preview: aiResponse.query_results_preview,
                error: aiResponse.error_message, // E.g. DDL block
                chart_type: aiResponse.suggested_chart_type
            };

            setMessages((prev) => [...prev, aiMsg]);
        } catch (error: any) {
            setMessages((prev) => [
                ...prev,
                { id: "err", role: "assistant", content: "", error: error.message || "Failed to reach agent backend." }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleClear = async () => {
        setMessages([]);
        await chatApi.clearHistory();
    };

    return (
        <div className="flex flex-col h-screen w-full bg-[#0a0a0a]">
            {/* Chat Header */}
            <div className="flex-none p-4 border-b border-[#222] bg-[#111] flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <div className="bg-emerald-500/10 p-2 rounded-lg">
                        <Database className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                        <h1 className="text-xl font-semibold text-zinc-100">SQL Data Analyst</h1>
                        <p className="text-xs text-zinc-400">Ask questions about your schema context in natural language.</p>
                    </div>
                </div>
                <button
                    onClick={handleClear}
                    className="p-2 text-zinc-400 hover:text-red-400 transition"
                    title="Clear Conversation"
                >
                    <Trash2 className="w-5 h-5" />
                </button>
            </div>

            {/* Scrollable Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-500 space-y-4">
                        <Database className="w-12 h-12 opacity-20" />
                        <p>Ask anything about AdventureWorks2025.</p>
                        <div className="flex gap-2 text-xs">
                            <span className="bg-zinc-800 px-3 py-1.5 rounded-full cursor-pointer hover:bg-zinc-700" onClick={() => setInput("Show me the top 5 most expensive products")}>
                                "Top 5 most expensive products?"
                            </span>
                            <span className="bg-zinc-800 px-3 py-1.5 rounded-full cursor-pointer hover:bg-zinc-700" onClick={() => setInput("Count all customers")}>
                                "Count all customers"
                            </span>
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={cn("flex w-full", msg.role === "user" ? "justify-end" : "justify-start")}>
                        <div className={cn("max-w-[85%] rounded-lg p-5", msg.role === "user" ? "bg-emerald-600 text-white" : "bg-[#111] border border-[#222] text-zinc-200")}>

                            {/* AI Error Rendering */}
                            {msg.error && (
                                <div className="mb-4 bg-red-950/30 border border-red-900/50 p-4 rounded text-red-400 flex items-start gap-3">
                                    <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                    <p className="text-sm font-mono leading-relaxed">{msg.error}</p>
                                </div>
                            )}

                            {/* AI SQL Execution Block rendering */}
                            {msg.role === "assistant" && msg.sql_executed && (
                                <div className="mb-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2 text-xs text-zinc-400 font-medium">
                                            <Code2 className="w-4 h-4" />
                                            Generated T-SQL
                                        </div>
                                        <div className="text-[10px] text-zinc-500 font-mono bg-[#1a1a1a] px-2 py-1 rounded">
                                            {msg.execution_time_ms ? `${msg.execution_time_ms.toFixed(0)} ms` : ""}
                                        </div>
                                    </div>
                                    <pre className="p-3 bg-zinc-950 rounded border border-zinc-800 overflow-x-auto text-[13px] text-sky-400 font-mono leading-relaxed">
                                        {msg.sql_executed}
                                    </pre>
                                </div>
                            )}

                            {/* Core Text Content */}
                            {msg.content && (
                                <div className="prose prose-invert max-w-none text-[15px] leading-relaxed">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                            )}

                            {/* Results Table (Very Basic generic renderer) */}
                            {msg.results_preview && msg.results_preview.length > 0 && (
                                <div className="mt-5 overflow-x-auto bg-[#050505] border border-[#222] rounded overflow-hidden">
                                    <table className="w-full text-left text-sm whitespace-nowrap">
                                        <thead className="bg-[#1a1a1a] border-b border-[#333]">
                                            <tr>
                                                {Object.keys(msg.results_preview[0]).map(key => (
                                                    <th key={key} className="px-4 py-3 font-medium text-zinc-300">
                                                        {key}
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-[#1a1a1a]">
                                            {msg.results_preview.map((row, i) => (
                                                <tr key={i} className="hover:bg-[#111]">
                                                    {Object.values(row).map((val: any, j) => (
                                                        <td key={j} className="px-4 py-2 text-zinc-400 max-w-[200px] truncate">
                                                            {String(val)}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-[#111] border border-[#222] p-4 rounded-lg flex items-center space-x-3 text-zinc-400">
                            <Loader2 className="w-5 h-5 animate-spin text-emerald-500" />
                            <span className="text-sm font-medium animate-pulse">Introspecting schema and generating code...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Form Footer */}
            <div className="flex-none p-4 md:p-6 bg-[#0a0a0a] border-t border-[#222]">
                <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="E.g., Which product subcategories have the highest list prices?"
                        className="w-full bg-[#111] border border-[#333] text-white rounded-xl pl-4 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-shadow"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 top-2 bottom-2 p-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                        <Send className="w-5 h-5 ml-1" />
                    </button>
                </form>
            </div>
        </div>
    );
}
