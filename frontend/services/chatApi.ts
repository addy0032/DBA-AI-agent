import { ChatResponsePayload } from "@/types/chat";
import { dbaApi } from "./api"; // Resusing the core configured Axios instance

export const chatApi = {
    async sendMessage(userMessage: string, sessionId: string = "default_session"): Promise<ChatResponsePayload> {
        // dbaApi already maps standard responses and throws on interceptor failures
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/chat/message`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                user_message: userMessage,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`Chat API failed: ${response.statusText}`);
        }

        return response.json();
    },

    async clearHistory(sessionId: string = "default_session") {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/chat/history?session_id=${sessionId}`, {
            method: "DELETE"
        });
        return response.ok;
    }
}
