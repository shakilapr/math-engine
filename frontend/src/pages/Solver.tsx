import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Send, Image as ImageIcon, RotateCcw, Check, ChevronRight, ChevronDown, Copy, X, AlertTriangle, MessageSquare, Loader2, PanelRightClose, PanelRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { MathRenderer } from '@/components/MathRenderer';
import { ChatSidebar } from '@/components/ChatSidebar';
import { SplitPane } from '@/components/SplitPane';
import { StepProgress, type StepEventData } from '@/components/StepProgress';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';

const API = 'http://localhost:8000/api';

interface Step {
    step_number: number;
    description: string;
    latex: string;
    python_code: string;
    result: string;
}

interface Verification {
    library: string;
    result: string;
    matches: boolean;
    code: string;
}

interface Viz {
    title: string;
    image_url: string;
    description: string;
}

export interface SolveResponse {
    success: boolean;
    problem_latex: string;
    category: string;
    steps: Step[];
    final_answer: string;
    final_answer_latex: string;
    generated_code: string;
    error?: string;
    verifications: Verification[];
    visualizations: Viz[];
}

type Provider = 'gemini' | 'claude' | 'deepseek' | 'openai';


export const SolverPage: React.FC = () => {
    const [input, setInput] = useState('');
    const [inputType, setInputType] = useState<'text' | 'latex' | 'image'>('text');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<SolveResponse | null>(null);
    const [showCode, setShowCode] = useState(false);
    const [chatOpen, setChatOpen] = useState(false);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [provider, setProvider] = useState<Provider>('deepseek');
    const [availableProviders, setAvailableProviders] = useState<Provider[]>([]);
    const [sessionId, setSessionId] = useState<string>('');

    // Real-time progress events
    const [stepEvents, setStepEvents] = useState<StepEventData[]>([]);

    // Step comments
    const [commentingStep, setCommentingStep] = useState<number | null>(null);
    const [stepComment, setStepComment] = useState('');
    const [commentLoading, setCommentLoading] = useState(false);

    // Sticky input — freeze input after solve
    const [frozenInput, setFrozenInput] = useState<string>('');
    const [hasSolved, setHasSolved] = useState(false);


    useEffect(() => {
        // Fetch configured keys
        axios.get(`${API}/keys`).then(res => {
            const configured: Provider[] = res.data.configured;
            setAvailableProviders(configured);

            if (configured.length === 1) {
                setProvider(configured[0]);
            } else if (configured.length > 0 && !configured.includes(provider)) {
                setProvider(configured[0]);
            }
        }).catch(console.error);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleSolve = async () => {
        if (!input.trim() && !imagePreview) return;
        setLoading(true);
        setResult(null);
        setStepEvents([]);
        setFrozenInput(input);
        setHasSolved(true);
        setCommentingStep(null);

        try {
            const response = await fetch(`${API}/solve?stream=true`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    input: inputType === 'image' ? imagePreview : input,
                    input_type: inputType,
                    provider: provider,
                    show_steps: true,
                    visualize: true,
                })
            });

            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);
                        if (event.type === 'step_event') {
                            setStepEvents(prev => [...prev, event as StepEventData]);
                        } else if (event.type === 'result') {
                            setResult(event.data);
                            if (event.session_id) {
                                setSessionId(event.session_id);
                            }
                        } else if (event.type === 'error') {
                            throw new Error(event.message);
                        }
                    } catch (e) {
                        console.error("Error parsing stream:", e);
                    }
                }
            }
        } catch (error: unknown) {
            const err = error as { message?: string };
            setResult({
                success: false,
                problem_latex: '',
                category: '',
                steps: [],
                final_answer: '',
                final_answer_latex: '',
                generated_code: '',
                verifications: [],
                visualizations: [],
                error: err.message || 'Failed to connect to backend',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleImageUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        processImageFile(file);
    }, []);

    const processImageFile = (file: File) => {
        const reader = new FileReader();
        reader.onload = (ev) => {
            const base64 = ev.target?.result as string;
            setImagePreview(base64);
            setInputType('image');
            setInput(file.name);
        };
        reader.readAsDataURL(file);
    };

    const handlePaste = useCallback((e: React.ClipboardEvent) => {
        const items = e.clipboardData?.items;
        if (!items) return;
        for (const item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                const file = item.getAsFile();
                if (file) processImageFile(file);
                return;
            }
        }
    }, []);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSolve();
        }
    };

    const copyCode = () => {
        if (result?.generated_code) {
            navigator.clipboard.writeText(result.generated_code);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const clearImage = () => {
        setImagePreview(null);
        setInputType('text');
        setInput('');
    };

    const handleCorrection = (correctedResult: SolveResponse) => {
        setResult(correctedResult);
    };

    const handleNewProblem = () => {
        setHasSolved(false);
        setResult(null);
        setStepEvents([]);
        setFrozenInput('');
        setCommentingStep(null);
        setSessionId('');
    };

    // Submit a comment on a step
    const submitStepComment = async (stepIndex: number) => {
        if (!stepComment.trim() || !sessionId) return;
        setCommentLoading(true);
        try {
            const res = await axios.post(`${API}/step/comment`, {
                step_index: stepIndex,
                comment: stepComment,
                session_id: sessionId,
                provider: provider,
            });
            if (res.data.success && res.data.edited_step && result) {
                const newSteps = [...result.steps];
                newSteps[stepIndex] = res.data.edited_step;
                setResult({ ...result, steps: newSteps });
                setStepComment('');
                setCommentingStep(null);
            }
        } catch (err) {
            console.error('Failed to submit step comment:', err);
        } finally {
            setCommentLoading(false);
        }
    };

    const tabs = [
        { id: 'text' as const, label: 'Text' },
        { id: 'latex' as const, label: 'LaTeX' },
        { id: 'image' as const, label: 'Image' },
    ];

    // ── Left Panel: Problem & Solution ──
    const leftPanel = (
        <div className="h-full overflow-auto">
            <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-semibold text-foreground">Solver</h1>
                        <p className="text-sm text-muted-foreground mt-0.5">
                            Enter a math problem to get a step-by-step solution
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        {hasSolved && (
                            <Button variant="outline" size="sm" onClick={handleNewProblem} className="gap-1.5 text-xs">
                                <RotateCcw className="h-3.5 w-3.5" />
                                New Problem
                            </Button>
                        )}
                        <Button
                            variant={chatOpen ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setChatOpen(!chatOpen)}
                            className="gap-1.5 text-xs"
                        >
                            {chatOpen ? <PanelRightClose className="h-3.5 w-3.5" /> : <PanelRight className="h-3.5 w-3.5" />}
                            {chatOpen ? 'Close Chat' : 'Open Chat'}
                        </Button>
                    </div>
                </div>

                {/* Sticky Input — always visible at top */}
                <div className={`border border-border rounded-lg bg-card overflow-hidden ${hasSolved ? 'opacity-80' : ''}`}>
                    {/* Frozen input display */}
                    {hasSolved ? (
                        <div className="px-4 py-3 flex items-center justify-between bg-muted/30">
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Problem</span>
                                <span className="text-sm text-foreground font-mono">{frozenInput}</span>
                            </div>
                            <Button variant="ghost" size="sm" onClick={handleNewProblem} className="text-xs h-7">
                                Edit
                            </Button>
                        </div>
                    ) : (
                        <>
                            {/* Tabs */}
                            <div className="flex border-b border-border items-center justify-between pr-2">
                                <div className="flex">
                                    {tabs.map(t => (
                                        <button
                                            key={t.id}
                                            onClick={() => { setInputType(t.id); if (t.id !== 'image') setImagePreview(null); }}
                                            className={`px-4 py-2.5 text-xs font-medium transition-colors relative ${inputType === t.id
                                                ? 'text-foreground'
                                                : 'text-muted-foreground hover:text-foreground'
                                                }`}
                                        >
                                            {t.label}
                                            {inputType === t.id && (
                                                <div className="absolute bottom-0 left-0 right-0 h-px bg-foreground" />
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Provider Selector */}
                            {availableProviders.length > 1 && (
                                <select
                                    value={provider}
                                    onChange={(e) => setProvider(e.target.value as Provider)}
                                    className="h-6 text-[10px] bg-card border border-border rounded px-2 focus:outline-none focus:ring-1 focus:ring-ring text-foreground hover:bg-accent transition-colors ml-4 mt-2"
                                >
                                    <option value="deepseek" disabled={!availableProviders.includes('deepseek')}>DeepSeek-V3</option>
                                    <option value="gemini" disabled={!availableProviders.includes('gemini')}>Gemini 2.0</option>
                                    <option value="claude" disabled={!availableProviders.includes('claude')}>Claude 3.5</option>
                                    <option value="openai" disabled={!availableProviders.includes('openai')}>GPT-4o</option>
                                </select>
                            )}

                            {/* Input area */}
                            <div className="p-4">
                                {inputType === 'image' && imagePreview ? (
                                    <div className="relative">
                                        <button
                                            onClick={clearImage}
                                            className="absolute top-2 right-2 z-10 p-1 rounded bg-black/60 hover:bg-black/80 text-white transition-colors"
                                        >
                                            <X className="h-3.5 w-3.5" />
                                        </button>
                                        <img
                                            src={imagePreview}
                                            alt="Math problem"
                                            className="max-h-56 rounded-md border border-border mx-auto"
                                        />
                                    </div>
                                ) : (
                                    <Textarea
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        onPaste={handlePaste}
                                        placeholder={
                                            inputType === 'latex'
                                                ? '\\int_0^\\pi \\sin(x)\\,dx'
                                                : 'e.g. What is the derivative of x^3 + 2x?'
                                        }
                                        className="min-h-[120px] text-sm bg-transparent border-0 focus-visible:ring-0 resize-none placeholder:text-muted-foreground/50 font-mono"
                                    />
                                )}
                            </div>

                            {/* Actions bar */}
                            <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/30">
                                <div className="flex items-center gap-2">
                                    <label className="cursor-pointer">
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            accept="image/*"
                                            className="hidden"
                                            onChange={handleImageUpload}
                                        />
                                        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
                                            <ImageIcon className="h-3.5 w-3.5" />
                                            <span>Upload image</span>
                                        </div>
                                    </label>
                                    <span className="text-[10px] text-muted-foreground/50">or paste with Ctrl+V</span>
                                </div>
                                <Button
                                    onClick={handleSolve}
                                    disabled={loading || (!input.trim() && !imagePreview)}
                                    size="sm"
                                    className="gap-1.5"
                                >
                                    {loading ? <RotateCcw className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                                    {loading ? 'Solving...' : 'Solve'}
                                </Button>
                            </div>
                        </>
                    )}
                </div>

                {/* Real-time Progress */}
                <StepProgress events={stepEvents} isActive={loading} />

                {/* Error */}
                {result && !result.success && (
                    <div className="flex items-start gap-3 p-4 rounded-lg border border-red-500/20 bg-red-500/5 text-sm">
                        <AlertTriangle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
                        <div>
                            <p className="font-medium text-red-400">Error</p>
                            <p className="text-red-300/80 mt-0.5">{result.error}</p>
                        </div>
                    </div>
                )}

                {/* Results */}
                {result && result.success && (
                    <div className="space-y-4">

                        {/* Final Answer */}
                        <div className="border border-border rounded-lg bg-card overflow-hidden">
                            <div className="px-4 py-2.5 border-b border-border flex items-center justify-between bg-muted/30">
                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Answer</span>
                                {result.category && (
                                    <span className="text-[10px] font-mono text-muted-foreground bg-accent px-2 py-0.5 rounded">
                                        {result.category.replace('_', ' ')}
                                    </span>
                                )}
                            </div>
                            <div className="px-6 py-6 text-center">
                                <div className="text-2xl">
                                    <MathRenderer content={result.final_answer_latex || result.final_answer} block />
                                </div>
                            </div>
                            {/* Verification */}
                            {result.verifications.length > 0 && (
                                <div className="px-4 py-3 border-t border-border flex items-center gap-2 flex-wrap">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-wider mr-1">Verified by</span>
                                    {result.verifications.map((v, i) => (
                                        <span
                                            key={i}
                                            title={`Result: ${v.result}`}
                                            className={`inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded font-mono ${v.matches
                                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                                }`}
                                        >
                                            <Check className="h-2.5 w-2.5" />
                                            {v.library}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Visualizations */}
                        {result.visualizations.length > 0 && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {result.visualizations.map((vis, i) => (
                                    <div key={i} className="border border-border rounded-lg bg-card overflow-hidden">
                                        <div className="px-3 py-2 border-b border-border text-xs font-medium text-muted-foreground">
                                            {vis.title}
                                        </div>
                                        <div className="p-3 flex items-center justify-center bg-black/20">
                                            <img
                                                src={`${API.replace('/api', '')}${vis.image_url}`}
                                                alt={vis.title}
                                                className="max-h-64 object-contain rounded"
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Steps with comment icons */}
                        {result.steps.length > 0 && (
                            <div className="border border-border rounded-lg bg-card overflow-hidden">
                                <div className="px-4 py-2.5 border-b border-border bg-muted/30">
                                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                        Step-by-step solution
                                    </span>
                                </div>
                                <div className="divide-y divide-border">
                                    {result.steps.map((step, idx) => (
                                        <div key={idx} className="px-4 py-4 group">
                                            <div className="flex items-center gap-2.5 mb-2">
                                                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary text-[10px] font-bold shrink-0">
                                                    {step.step_number}
                                                </span>
                                                <span className="text-xs font-medium text-muted-foreground flex-1">Step {step.step_number}</span>

                                                {/* Comment icon */}
                                                <button
                                                    onClick={() => {
                                                        setCommentingStep(commentingStep === idx ? null : idx);
                                                        setStepComment('');
                                                    }}
                                                    className={`p-1 rounded transition-colors ${commentingStep === idx
                                                        ? 'bg-primary/10 text-primary'
                                                        : 'text-muted-foreground/40 hover:text-muted-foreground opacity-0 group-hover:opacity-100'
                                                        }`}
                                                    title="Comment on this step"
                                                >
                                                    <MessageSquare className="h-3.5 w-3.5" />
                                                </button>
                                            </div>

                                            <div className="prose prose-invert prose-sm max-w-none ml-[30px] prose-p:text-gray-300 prose-p:leading-relaxed prose-p:my-1">
                                                <ReactMarkdown>{step.description}</ReactMarkdown>
                                            </div>

                                            {step.latex && (
                                                <div className="mt-3 ml-[30px] bg-muted/50 rounded-md p-3 overflow-x-auto border border-border">
                                                    <MathRenderer content={step.latex} block />
                                                </div>
                                            )}

                                            {step.result && (
                                                <div className="mt-2 ml-[30px] flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground">
                                                    <ChevronRight className="h-3 w-3" />
                                                    <span>= {step.result}</span>
                                                </div>
                                            )}

                                            {/* Inline comment box */}
                                            {commentingStep === idx && (
                                                <div className="mt-3 ml-[30px] border border-border rounded-lg bg-muted/20 p-3">
                                                    <textarea
                                                        value={stepComment}
                                                        onChange={(e) => setStepComment(e.target.value)}
                                                        placeholder="Describe what should change about this step..."
                                                        className="w-full bg-transparent text-sm text-foreground border-0 focus:outline-none resize-none min-h-[60px] placeholder:text-muted-foreground/50"
                                                        onKeyDown={(e) => {
                                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                                e.preventDefault();
                                                                submitStepComment(idx);
                                                            }
                                                        }}
                                                    />
                                                    <div className="flex items-center justify-end gap-2 mt-2">
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => { setCommentingStep(null); setStepComment(''); }}
                                                            className="text-xs h-7"
                                                        >
                                                            Cancel
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            onClick={() => submitStepComment(idx)}
                                                            disabled={commentLoading || !stepComment.trim()}
                                                            className="text-xs h-7 gap-1"
                                                        >
                                                            {commentLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                                                            Submit
                                                        </Button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Generated Code */}
                        {result.generated_code && (
                            <div className="border border-border rounded-lg bg-card overflow-hidden">
                                <button
                                    onClick={() => setShowCode(!showCode)}
                                    className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors"
                                >
                                    <span>Generated Python Code</span>
                                    {showCode ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                                </button>

                                {showCode && (
                                    <div className="border-t border-border relative">
                                        <button
                                            onClick={copyCode}
                                            className="absolute top-2 right-2 p-1.5 rounded bg-accent hover:bg-accent/80 text-muted-foreground hover:text-foreground transition-colors text-xs"
                                            title="Copy code"
                                        >
                                            {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                                        </button>
                                        <pre className="p-4 text-xs font-mono text-gray-300 overflow-x-auto bg-[#0a0a0a]">
                                            <code>{result.generated_code}</code>
                                        </pre>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );

    // ── Right Panel: Chat ──
    const rightPanel = (
        <ChatSidebar
            open={true}
            onClose={() => setChatOpen(false)}
            solveResult={result}
            onCorrection={handleCorrection}
            embedded={true}
        />
    );

    return (
        <div className="h-full flex">
            <SplitPane
                left={leftPanel}
                right={rightPanel}
                defaultSplit={65}
                minLeft={400}
                minRight={300}
                rightCollapsed={!chatOpen}
            />
        </div>
    );
};
