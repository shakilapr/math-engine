import React, { useState, useRef, useEffect } from 'react';
import { Send, X, MessageCircle, Loader2, Pencil } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AutoMath } from '@/components/MathRenderer';
import type { SolveResponse } from '@/pages/Solver';
import axios from 'axios';

const API = 'http://localhost:8000/api';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    isCorrection?: boolean;
}

interface ChatSidebarProps {
    open: boolean;
    onClose: () => void;
    solveResult?: SolveResponse | null;
    onCorrection?: (result: SolveResponse) => void;
}

function buildContext(result: SolveResponse | null | undefined): string {
    if (!result || !result.success) return '';

    const parts: string[] = [];
    parts.push(`Problem: ${result.problem_latex}`);
    parts.push(`Category: ${result.category}`);
    parts.push(`Final Answer: ${result.final_answer}`);

    if (result.steps.length > 0) {
        parts.push('\nSolution Steps:');
        result.steps.forEach(s => {
            parts.push(`  Step ${s.step_number}: ${s.description}`);
            if (s.latex) parts.push(`    Math: ${s.latex}`);
            if (s.result) parts.push(`    Result: ${s.result}`);
        });
    }

    if (result.verifications.length > 0) {
        parts.push('\nVerification:');
        result.verifications.forEach(v => {
            parts.push(`  ${v.library}: ${v.result} (${v.matches ? 'matches' : 'mismatch'})`);
        });
    }

    if (result.generated_code) {
        parts.push(`\nGenerated Code:\n${result.generated_code}`);
    }

    return parts.join('\n');
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({ open, onClose, solveResult, onCorrection }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        if (open) inputRef.current?.focus();
    }, [open]);

    const context = buildContext(solveResult);
    const hasContext = !!context;

    const sendMessage = async () => {
        if (!input.trim() || loading) return;
        const userMsg = input.trim();
        setInput('');

        // Detect correction intent
        const isCorrection = /\b(wrong|incorrect|mistake|should be|fix|correct|actually|error in step)\b/i.test(userMsg);

        setMessages(prev => [...prev, { role: 'user', content: userMsg, isCorrection }]);
        setLoading(true);

        try {
            // If correction detected and we have a solve result, re-solve with correction context
            if (isCorrection && solveResult && onCorrection) {
                const correctionContext = `Original problem: ${solveResult.problem_latex}\nUser correction: ${userMsg}\nPlease re-solve taking the correction into account.`;

                const res = await axios.post(`${API}/chat`, {
                    message: userMsg,
                    conversation_id: conversationId,
                    provider: 'gemini',
                    context: correctionContext,
                });
                setConversationId(res.data.conversation_id);
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: res.data.message + '\n\n*I\'ve noted this correction. You can re-solve the problem with the updated understanding.*'
                }]);
            } else {
                const res = await axios.post(`${API}/chat`, {
                    message: userMsg,
                    conversation_id: conversationId,
                    provider: 'gemini',
                    context: context,
                });
                setConversationId(res.data.conversation_id);
                setMessages(prev => [...prev, { role: 'assistant', content: res.data.message }]);
            }
        } catch {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Connection error. Check that the backend is running and API keys are configured in Settings.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    if (!open) return null;

    return (
        <div className="w-[360px] border-l border-border bg-card flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between px-4 h-14 border-b border-border shrink-0">
                <div className="flex items-center gap-2">
                    <MessageCircle className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Chat</span>
                </div>
                <Button variant="ghost" size="icon" onClick={onClose} className="h-7 w-7 text-muted-foreground hover:text-foreground">
                    <X className="h-3.5 w-3.5" />
                </Button>
            </div>

            {/* Context indicator */}
            {hasContext && (
                <div className="px-4 py-2 border-b border-border bg-muted/30 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span className="text-[11px] text-muted-foreground">
                        Context: {solveResult?.category?.replace('_', ' ') || 'current problem'}
                    </span>
                </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-auto p-4 space-y-3">
                {messages.length === 0 && (
                    <div className="text-center text-muted-foreground text-sm mt-12 space-y-3">
                        <MessageCircle className="h-8 w-8 mx-auto opacity-20" />
                        <div className="space-y-1">
                            <p className="text-xs">Ask questions about math</p>
                            {hasContext && (
                                <p className="text-[11px] text-muted-foreground/70">
                                    I have context about your current problem
                                </p>
                            )}
                        </div>
                    </div>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                            className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${msg.role === 'user'
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-muted text-foreground'
                                }`}
                        >
                            {msg.isCorrection && (
                                <div className="flex items-center gap-1 text-[10px] opacity-70 mb-1">
                                    <Pencil className="h-2.5 w-2.5" /> Correction
                                </div>
                            )}
                            <AutoMath text={msg.content} />
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-muted rounded-lg px-3 py-2">
                            <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="p-3 border-t border-border shrink-0">
                <div className="flex gap-2">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={hasContext ? 'Ask about this problem...' : 'Ask a question...'}
                        rows={1}
                        className="flex-1 resize-none rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground/50 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    />
                    <Button size="icon" onClick={sendMessage} disabled={!input.trim() || loading} className="shrink-0 h-9 w-9">
                        <Send className="h-3.5 w-3.5" />
                    </Button>
                </div>
            </div>
        </div>
    );
};
