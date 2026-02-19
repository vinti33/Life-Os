import { createContext, useContext, useState } from 'react';
import { chatService } from '../services/chatService';

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [sessions, setSessions] = useState([]);

    const loadSessions = async () => {
        try {
            const list = await chatService.getSessions();
            setSessions(list);
        } catch (e) { console.error(e); }
    };

    const loadSession = async (sessionId) => {
        setLoading(true);
        try {
            const data = await chatService.getSessionHistory(sessionId);
            // Transform backend messages to frontend format
            const history = data.messages.map(m => ({
                role: m.role,
                content: m.content,
                timestamp: m.timestamp,
                questions: m.questions || [],
                actions: m.actions || []
            }));
            setMessages(history);
            setCurrentSessionId(sessionId);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const startNewSession = () => {
        setMessages([]);
        setCurrentSessionId(null);
    };

    const sendMessage = async (content) => {
        setLoading(true);
        const userMsg = { role: 'user', content, timestamp: new Date() };
        setMessages((prev) => [...prev, userMsg]);

        try {
            let refinedContent = content;
            if (content.toLowerCase().includes('next task')) {
                refinedContent += " (Context: Check active plan for next scheduled task)";
            }

            const data = await chatService.sendMessage(refinedContent, currentSessionId);

            // Update session ID if this was the first message
            if (!currentSessionId && data.session_id) {
                setCurrentSessionId(data.session_id);
                loadSessions(); // Refresh list to show new chat
            }

            const aiReply = {
                role: 'assistant',
                content: data.message || data.reply, // Support both new and legacy
                questions: data.clarification_questions || [],
                actions: data.action ? [data.action] : (data.actions || []), // Single or array
                timestamp: new Date()
            };
            setMessages((prev) => [...prev, aiReply]);
            return data;
        } catch (error) {
            console.error('Failed to send message', error);
        } finally {
            setLoading(false);
        }
    };

    const addLocalMessage = (role, content) => {
        setMessages((prev) => [...prev, { role, content, timestamp: new Date() }]);
    };

    return (
        <ChatContext.Provider value={{
            messages, loading, sendMessage, addLocalMessage,
            sessions, loadSessions, loadSession, startNewSession, currentSessionId
        }}>
            {children}
        </ChatContext.Provider>
    );
};

export const useChat = () => useContext(ChatContext);
