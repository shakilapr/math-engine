import React, { useEffect, useRef } from 'react';
import { Brain, FileCode, Zap, CheckCircle2, Pencil, AlertTriangle, Code2 } from 'lucide-react';

export interface StepEventData {
    type: string;
    step_index: number;
    status: string;
    script_id: string;
    script_name: string;
    code: string;
    result: string;
    thinking: string;
    diff: string;
    description: string;
    latex: string;
}

interface StepProgressProps {
    events: StepEventData[];
    isActive: boolean;
}

const eventIcon = (type: string) => {
    switch (type) {
        case 'thinking': return <Brain className="h-3.5 w-3.5 text-blue-400" />;
        case 'script_selected': return <FileCode className="h-3.5 w-3.5 text-cyan-400" />;
        case 'code_writing': return <Code2 className="h-3.5 w-3.5 text-amber-400" />;
        case 'executing': return <Zap className="h-3.5 w-3.5 text-yellow-400" />;
        case 'step_result': return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
        case 'step_edited': return <Pencil className="h-3.5 w-3.5 text-purple-400" />;
        case 'error': return <AlertTriangle className="h-3.5 w-3.5 text-red-400" />;
        default: return <Zap className="h-3.5 w-3.5 text-muted-foreground" />;
    }
};

const eventLabel = (type: string) => {
    switch (type) {
        case 'thinking': return 'Thinking';
        case 'script_selected': return 'Script Selected';
        case 'code_writing': return 'Writing Code';
        case 'executing': return 'Executing';
        case 'step_result': return 'Result';
        case 'step_edited': return 'Edited';
        case 'error': return 'Error';
        default: return type;
    }
};

export const StepProgress: React.FC<StepProgressProps> = ({ events, isActive }) => {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [events.length]);

    if (events.length === 0 && !isActive) return null;

    return (
        <div className="border border-border rounded-lg bg-card overflow-hidden">
            <div className="px-4 py-2.5 border-b border-border bg-muted/30 flex items-center gap-2">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Live Progress
                </span>
                {isActive && (
                    <span className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-[10px] text-emerald-400">Active</span>
                    </span>
                )}
            </div>
            <div
                ref={scrollRef}
                className="max-h-64 overflow-y-auto divide-y divide-border/50"
            >
                {events.map((event, idx) => (
                    <div key={idx} className="px-4 py-2.5 flex items-start gap-2.5 animate-fadeIn">
                        <div className="mt-0.5 shrink-0">
                            {eventIcon(event.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                                    {eventLabel(event.type)}
                                </span>
                                {event.step_index >= 0 && (
                                    <span className="text-[10px] font-mono text-muted-foreground/60">
                                        Step {event.step_index + 1}
                                    </span>
                                )}
                            </div>
                            {/* Content */}
                            {event.thinking && (
                                <p className="text-xs text-foreground/80 mt-0.5 leading-relaxed">
                                    {event.thinking}
                                </p>
                            )}
                            {event.status && !event.thinking && (
                                <p className="text-xs text-foreground/80 mt-0.5">
                                    {event.status}
                                </p>
                            )}
                            {event.script_name && (
                                <p className="text-xs mt-0.5">
                                    <span className="text-muted-foreground">Script: </span>
                                    <span className="font-mono text-cyan-400">{event.script_name}</span>
                                </p>
                            )}
                            {event.code && event.type === 'code_writing' && (
                                <pre className="mt-1.5 p-2 rounded bg-[#0a0a0a] border border-border text-[10px] font-mono text-gray-400 overflow-x-auto max-h-24">
                                    <code>{event.code.slice(0, 300)}{event.code.length > 300 ? '...' : ''}</code>
                                </pre>
                            )}
                            {event.result && event.type === 'step_result' && (
                                <p className="text-xs mt-0.5 font-mono text-emerald-400">
                                    = {event.result}
                                </p>
                            )}
                            {event.diff && (
                                <p className="text-xs mt-0.5 text-purple-300 italic">
                                    {event.diff}
                                </p>
                            )}
                        </div>
                    </div>
                ))}
                {isActive && events.length > 0 && (
                    <div className="px-4 py-2.5 flex items-center gap-2">
                        <div className="w-3.5 h-3.5 flex items-center justify-center">
                            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                        </div>
                        <span className="text-xs text-muted-foreground">Processing...</span>
                    </div>
                )}
            </div>
        </div>
    );
};
