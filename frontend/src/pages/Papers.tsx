import React, { useState } from 'react';
import { Upload, FileText, ChevronDown, ChevronRight, Search, Replace, Loader2, ArrowRight, Sigma } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { MathRenderer } from '@/components/MathRenderer';
import axios from 'axios';

const API = 'http://localhost:8000/api';

interface PDFSection {
    section_title: string;
    original_text: string;
    math_expressions: string[];
    explanations: string[];
}

interface PDFAnalysis {
    success: boolean;
    filename: string;
    total_sections: number;
    sections: PDFSection[];
    error?: string;
}

export const PapersPage: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [analysis, setAnalysis] = useState<PDFAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());
    const [searchTerm, setSearchTerm] = useState('');
    const [replaceTerm, setReplaceTerm] = useState('');
    const [editedContent, setEditedContent] = useState<Record<number, string>>({});
    const [showSearch, setShowSearch] = useState(false);

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('provider', 'gemini');
            const res = await axios.post(`${API}/pdf/analyze`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setAnalysis(res.data);
            const all = new Set<number>();
            res.data.sections?.forEach((_: PDFSection, i: number) => all.add(i));
            setExpandedSections(all);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const toggleSection = (idx: number) => {
        setExpandedSections(prev => {
            const next = new Set(prev);
            if (next.has(idx)) next.delete(idx);
            else next.add(idx);
            return next;
        });
    };

    const getContent = (idx: number, original: string) => editedContent[idx] ?? original;

    const handleSearchReplace = () => {
        if (!searchTerm || !analysis) return;
        const updated = { ...editedContent };
        analysis.sections.forEach((section, idx) => {
            const content = getContent(idx, section.original_text);
            if (content.includes(searchTerm)) {
                updated[idx] = content.replaceAll(searchTerm, replaceTerm);
            }
        });
        setEditedContent(updated);
    };

    return (
        <div className="h-full overflow-auto">
            <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-xl font-semibold text-foreground">Research Papers</h1>
                    <p className="text-sm text-muted-foreground mt-0.5">
                        Upload a PDF to extract and analyze mathematical content
                    </p>
                </div>

                {/* Upload */}
                {!analysis && (
                    <div className="border border-dashed border-border rounded-lg p-10 text-center bg-card">
                        <Upload className="h-8 w-8 text-muted-foreground/40 mx-auto mb-4" />
                        <p className="text-sm font-medium text-foreground mb-1">Drop a PDF here or click to browse</p>
                        <p className="text-xs text-muted-foreground mb-6">
                            Extracts formulas, verifies calculations, provides explanations
                        </p>

                        <div className="flex flex-col items-center gap-3">
                            <label className="cursor-pointer">
                                <input type="file" accept=".pdf" className="hidden" onChange={e => setFile(e.target.files?.[0] || null)} />
                                <span className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-muted text-sm font-medium text-foreground hover:bg-accent transition-colors border border-border">
                                    <FileText className="h-3.5 w-3.5" />
                                    {file ? file.name : 'Select PDF'}
                                </span>
                            </label>
                            <Button onClick={handleUpload} disabled={!file || loading} size="sm" className="gap-1.5">
                                {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ArrowRight className="h-3.5 w-3.5" />}
                                {loading ? 'Analyzing...' : 'Analyze'}
                            </Button>
                        </div>
                    </div>
                )}

                {/* Toolbar */}
                {analysis && (
                    <div className="border border-border rounded-lg bg-card p-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-mono text-muted-foreground truncate max-w-[250px]">{analysis.filename}</span>
                            <div className="flex items-center gap-2">
                                <Button variant="ghost" size="sm" onClick={() => setShowSearch(!showSearch)} className="gap-1.5 text-xs h-7">
                                    <Search className="h-3 w-3" /> Find & Replace
                                </Button>
                                <Button variant="ghost" size="sm" onClick={() => { setAnalysis(null); setFile(null); setEditedContent({}); }} className="text-xs h-7">
                                    New
                                </Button>
                            </div>
                        </div>
                        {showSearch && (
                            <div className="grid grid-cols-1 md:grid-cols-[1fr,1fr,auto] gap-2 mt-3 pt-3 border-t border-border">
                                <div className="relative">
                                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                                    <Input placeholder="Find..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="pl-8 h-8 text-xs" />
                                </div>
                                <div className="relative">
                                    <Replace className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                                    <Input placeholder="Replace..." value={replaceTerm} onChange={e => setReplaceTerm(e.target.value)} className="pl-8 h-8 text-xs" />
                                </div>
                                <Button onClick={handleSearchReplace} size="sm" variant="outline" className="h-8 text-xs">Replace All</Button>
                            </div>
                        )}
                    </div>
                )}

                {/* Sections */}
                {analysis && analysis.success && (
                    <div className="space-y-3">
                        {analysis.sections.map((section, idx) => (
                            <div key={idx} className="border border-border rounded-lg bg-card overflow-hidden">
                                <button
                                    onClick={() => toggleSection(idx)}
                                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/30 transition-colors text-left"
                                >
                                    <div className="flex items-center gap-2">
                                        {expandedSections.has(idx) ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />}
                                        <span className="text-sm font-medium">{section.section_title}</span>
                                    </div>
                                    {section.math_expressions.length > 0 && (
                                        <span className="inline-flex items-center gap-1 text-[10px] font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/15">
                                            <Sigma className="h-2.5 w-2.5" /> {section.math_expressions.length}
                                        </span>
                                    )}
                                </button>

                                {expandedSections.has(idx) && (
                                    <div className="border-t border-border">
                                        <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-border">
                                            {/* Content */}
                                            <div className="p-4">
                                                <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-2">Content</div>
                                                <Textarea
                                                    value={getContent(idx, section.original_text)}
                                                    onChange={e => setEditedContent(prev => ({ ...prev, [idx]: e.target.value }))}
                                                    className="min-h-[260px] text-xs font-mono leading-relaxed resize-y bg-transparent border-0 focus-visible:ring-0 p-0"
                                                />
                                            </div>
                                            {/* Analysis */}
                                            <div className="p-4 space-y-4 bg-muted/20">
                                                {section.math_expressions.length > 0 && (
                                                    <div>
                                                        <div className="text-[10px] font-medium text-blue-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                                                            <Sigma className="h-2.5 w-2.5" /> Extracted Math
                                                        </div>
                                                        <div className="space-y-2">
                                                            {section.math_expressions.map((expr, i) => (
                                                                <div key={i} className="bg-muted rounded-md p-2.5 border border-border overflow-x-auto">
                                                                    <MathRenderer content={expr} block />
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {section.explanations.length > 0 && (
                                                    <div>
                                                        <div className="text-[10px] font-medium text-emerald-400 uppercase tracking-wider mb-2">Explanations</div>
                                                        <div className="space-y-2">
                                                            {section.explanations.map((exp, i) => (
                                                                <div key={i} className="text-xs text-gray-400 pl-3 border-l-2 border-emerald-500/30 leading-relaxed">
                                                                    {exp}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {analysis && !analysis.success && (
                    <div className="p-4 border border-red-500/20 bg-red-500/5 text-red-400 text-sm rounded-lg">
                        {analysis.error}
                    </div>
                )}
            </div>
        </div>
    );
};
