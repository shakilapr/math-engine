import React, { useState, useEffect } from 'react';
import axios from 'axios';
import type { HistoryEntry, ImprovementProposal } from '../types/SelfEvolution';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Activity, GitCommit, CheckCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/self-edit';

export const SelfEvolutionPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'history' | 'improve'>('history');
    const [history, setHistory] = useState<HistoryEntry[]>([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

    // Improve form state
    const [improveForm, setImproveForm] = useState({
        problem_latex: '',
        error: '',
        code: '',
        traceback: '',
        category: 'other'
    });
    const [improving, setImproving] = useState(false);
    const [proposal, setProposal] = useState<ImprovementProposal | null>(null);

    const fetchHistory = async () => {
        setLoadingHistory(true);
        try {
            const res = await axios.get(`${API_BASE}/history?limit=50`);
            if (Array.isArray(res.data)) {
                setHistory(res.data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingHistory(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'history') fetchHistory();
    }, [activeTab]);

    const handleImprove = async () => {
        setImproving(true);
        setProposal(null);
        try {
            const res = await axios.post(`${API_BASE}/improve`, improveForm);
            setProposal(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setImproving(false);
        }
    };

    return (
        <div className="h-full overflow-auto">
            <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-semibold text-foreground">Self-Evolution Dashboard</h1>
                        <p className="text-sm text-muted-foreground mt-0.5">
                            Monitor and control the engine's self-improvement capabilities
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant={activeTab === 'history' ? 'default' : 'outline'} onClick={() => setActiveTab('history')} size="sm" className="h-8 text-xs gap-1.5">
                            <GitCommit className="h-3.5 w-3.5" /> History
                        </Button>
                        <Button variant={activeTab === 'improve' ? 'default' : 'outline'} onClick={() => setActiveTab('improve')} size="sm" className="h-8 text-xs gap-1.5">
                            <Activity className="h-3.5 w-3.5" /> Manual Trigger
                        </Button>
                    </div>
                </div>

                {activeTab === 'history' && (
                    <Card className="border-border bg-card">
                        <CardHeader>
                            <CardTitle>Edit History</CardTitle>
                            <CardDescription>Recent modifications made by the self-editing agent.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loadingHistory ? (
                                <div className="flex justify-center p-8"><Loader2 className="animate-spin text-primary" /></div>
                            ) : (
                                <div className="space-y-4">
                                    {history.map((entry) => (
                                        <div key={entry.backup_id} className="flex items-start gap-4 p-4 border border-border rounded-lg bg-background/50">
                                            <GitCommit className="mt-1 h-5 w-5 text-muted-foreground" />
                                            <div>
                                                <div className="font-semibold text-foreground">{entry.description}</div>
                                                <div className="text-sm text-muted-foreground">
                                                    {new Date(entry.timestamp * 1000).toLocaleString()} • <span className="uppercase text-xs font-bold">{entry.operation}</span> • {entry.files.length} file(s)
                                                </div>
                                                <div className="mt-2 flex gap-2 flex-wrap">
                                                    {entry.files.map(f => (
                                                        <span key={f} className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded font-mono border border-border">{f}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {history.length === 0 && <div className="text-center text-muted-foreground p-8">No history found.</div>}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {activeTab === 'improve' && (
                    <div className="grid gap-8 md:grid-cols-2">
                        <Card className="border-border bg-card">
                            <CardHeader>
                                <CardTitle>Trigger Improvement</CardTitle>
                                <CardDescription>Simulate a failure to test the improvement loop.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Problem LaTeX</label>
                                    <Input
                                        value={improveForm.problem_latex}
                                        onChange={e => setImproveForm({ ...improveForm, problem_latex: e.target.value })}
                                        placeholder="e.g. \int x^2 dx"
                                        className="bg-background border-input"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Error Message</label>
                                    <Input
                                        value={improveForm.error}
                                        onChange={e => setImproveForm({ ...improveForm, error: e.target.value })}
                                        placeholder="e.g. ZeroDivisionError"
                                        className="bg-background border-input"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Failed Code</label>
                                    <Textarea
                                        value={improveForm.code}
                                        onChange={e => setImproveForm({ ...improveForm, code: e.target.value })}
                                        placeholder="def solve(): ..."
                                        className="font-mono text-xs h-32 bg-background border-input"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Traceback</label>
                                    <Textarea
                                        value={improveForm.traceback}
                                        onChange={e => setImproveForm({ ...improveForm, traceback: e.target.value })}
                                        placeholder="Traceback (most recent call last)..."
                                        className="font-mono text-xs h-32 bg-background border-input"
                                    />
                                </div>
                                <Button onClick={handleImprove} disabled={improving} className="w-full">
                                    {improving && <Loader2 className="animate-spin mr-2 h-4 w-4" />}
                                    Analyze & Propose Fix
                                </Button>
                            </CardContent>
                        </Card>

                        <Card className="border-border bg-card flex flex-col">
                            <CardHeader>
                                <CardTitle>Analysis Result</CardTitle>
                                <CardDescription>Proposed improvements from the agent.</CardDescription>
                            </CardHeader>
                            <CardContent className="flex-1">
                                {proposal ? (
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-2 text-emerald-500 font-medium bg-emerald-500/10 p-3 rounded-md border border-emerald-500/20">
                                            <CheckCircle className="h-5 w-5" />
                                            <span>Analysis Complete ({proposal.confidence} confidence)</span>
                                        </div>
                                        <div className="bg-muted p-4 rounded-lg text-sm border border-border">
                                            {proposal.analysis}
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-semibold mb-2 text-foreground">Affected Files</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {proposal.files?.map(f => (
                                                    <span key={f} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded font-mono border border-primary/20">{f}</span>
                                                ))}
                                                {(!proposal.files || proposal.files.length === 0) && <span className="text-sm text-muted-foreground italic">No files modified</span>}
                                            </div>
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-semibold mb-2 text-foreground">Patch Hunks</h4>
                                            <div className="space-y-2">
                                                {proposal.hunks?.map((hunk, i) => (
                                                    <div key={i} className="border border-border rounded bg-card overflow-hidden">
                                                        <div className="bg-muted px-3 py-1.5 text-xs font-mono border-b border-border flex justify-between items-center">
                                                            <span className="text-foreground font-medium">{hunk.path}</span>
                                                            <span className={`uppercase text-[10px] font-bold px-1.5 py-0.5 rounded ${hunk.kind === 'update' ? 'bg-blue-500/20 text-blue-400' :
                                                                hunk.kind === 'add' ? 'bg-green-500/20 text-green-400' :
                                                                    'bg-red-500/20 text-red-400'
                                                                }`}>{hunk.kind}</span>
                                                        </div>
                                                        <div className="relative overflow-x-auto bg-[#1e1e1e] p-2">
                                                            <pre className="text-[10px] font-mono text-gray-300">
                                                                {hunk.kind === 'update' ? (
                                                                    <>
                                                                        <div className="text-red-400/70 select-none">--- old</div>
                                                                        <div className="text-red-300">{hunk.old_text}</div>
                                                                        <div className="text-emerald-400/70 mt-2 select-none">+++ new</div>
                                                                        <div className="text-emerald-300">{hunk.new_text}</div>
                                                                    </>
                                                                ) : hunk.content}
                                                            </pre>
                                                        </div>
                                                    </div>
                                                ))}
                                                {(!proposal.hunks || proposal.hunks.length === 0) && <span className="text-sm text-muted-foreground italic">No code changes proposed.</span>}
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-muted-foreground border-2 border-dashed border-border rounded-lg bg-muted/5">
                                        <Activity className="h-8 w-8 mb-2 opacity-50" />
                                        <p>No analysis results yet.</p>
                                        <p className="text-xs text-muted-foreground/70 mt-1">Submit the form to trigger analysis</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>
        </div>
    );
};
