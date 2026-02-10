import React from 'react';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

interface MathRendererProps {
    content: string;
    block?: boolean;
    className?: string;
}

export const MathRenderer: React.FC<MathRendererProps> = ({
    content,
    block = false,
    className = ""
}) => {
    try {
        // If content contains specific LaTeX delimiters, render them
        // Otherwise render as given
        if (block) {
            return <div className={`overflow-x-auto ${className}`}><BlockMath math={content} /></div>;
        }
        return <span className={className}><InlineMath math={content} /></span>;
    } catch (e) {
        console.error("KaTeX error:", e);
        return <span className="text-red-500 font-mono text-sm">{content}</span>;
    }
};

export const AutoMath: React.FC<{ text: string }> = ({ text }) => {
    // Simple parser to detect math requiring display mode vs inline
    // This is a naive implementation, a robust one would use a proper parser
    if (!text) return null;

    const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g);

    return (
        <span>
            {parts.map((part, i) => {
                if (part.startsWith('$$') && part.endsWith('$$')) {
                    return <MathRenderer key={i} content={part.slice(2, -2)} block />;
                }
                if (part.startsWith('$') && part.endsWith('$')) {
                    return <MathRenderer key={i} content={part.slice(1, -1)} />;
                }
                return <span key={i}>{part}</span>;
            })}
        </span>
    );
};
