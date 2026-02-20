export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    sql_executed?: string;
    execution_time_ms?: number;
    results_preview?: Record<string, any>[];
    chart_type?: "bar" | "line" | "pie" | "none";
    error?: string;
}

export interface ChatResponsePayload {
    generated_sql?: string;
    explanation: string;
    confidence: number;
    execution_time_ms: number;
    query_results_preview: Record<string, any>[];
    error_message?: string;
    suggested_chart_type?: "bar" | "line" | "pie" | "none";
}
