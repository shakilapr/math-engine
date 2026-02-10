import React, { useState, useEffect } from 'react';
import { Save, Eye, EyeOff, Key, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import axios from 'axios';
import { toast } from 'react-hot-toast';

const API = 'http://localhost:8000/api';

interface APIKeys {
    gemini: string;
    claude: string;
    deepseek: string;
    openai: string;
}

export const SettingsPage: React.FC = () => {
    const [keys, setKeys] = useState<APIKeys>({ gemini: '', claude: '', deepseek: '', openai: '' });
    const [status, setStatus] = useState<Record<keyof APIKeys, boolean>>({
        gemini: false, claude: false, deepseek: false, openai: false
    });
    const [showKey, setShowKey] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => { fetchKeys(); }, []);

    const fetchKeys = async () => {
        try {
            const res = await axios.get(`${API}/settings/keys`);
            if (res.data.status) setStatus(res.data.status);
        } catch (error) {
            console.error(error);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            const toSend: Partial<APIKeys> = {};
            (Object.keys(keys) as Array<keyof APIKeys>).forEach(k => {
                if (keys[k]) toSend[k] = keys[k];
            });
            await axios.post(`${API}/settings/keys`, toSend);
            await fetchKeys();
            setKeys({ gemini: '', claude: '', deepseek: '', openai: '' });
            toast.success('API keys updated');
        } catch {
            toast.error('Failed to save API keys');
        } finally {
            setLoading(false);
        }
    };

    const providers = [
        { id: 'gemini', name: 'Google Gemini' },
        { id: 'claude', name: 'Anthropic Claude' },
        { id: 'deepseek', name: 'DeepSeek' },
        { id: 'openai', name: 'OpenAI' },
    ];

    return (
        <div className="h-full overflow-auto">
            <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-xl font-semibold text-foreground">Settings</h1>
                    <p className="text-sm text-muted-foreground mt-0.5">
                        Configure API providers and preferences
                    </p>
                </div>

                {/* API Keys */}
                <div className="border border-border rounded-lg bg-card overflow-hidden">
                    <div className="px-4 py-3 border-b border-border bg-muted/30">
                        <h2 className="text-sm font-medium">LLM Providers</h2>
                        <p className="text-[11px] text-muted-foreground mt-0.5">Keys are stored in memory only</p>
                    </div>

                    <div className="divide-y divide-border">
                        {providers.map(p => (
                            <div key={p.id} className="px-4 py-4">
                                <div className="flex items-center justify-between mb-2">
                                    <label className="text-sm font-medium">{p.name}</label>
                                    {status[p.id as keyof APIKeys] ? (
                                        <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/15">
                                            <CheckCircle2 className="h-2.5 w-2.5" /> Active
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/15">
                                            <AlertCircle className="h-2.5 w-2.5" /> Missing
                                        </span>
                                    )}
                                </div>
                                <div className="relative">
                                    <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                                    <Input
                                        type={showKey === p.id ? 'text' : 'password'}
                                        placeholder={status[p.id as keyof APIKeys] ? '••••••••••••' : `Enter API key`}
                                        value={keys[p.id as keyof APIKeys]}
                                        onChange={(e) => setKeys({ ...keys, [p.id]: e.target.value })}
                                        className="pl-9 pr-9 bg-background border-border font-mono text-xs h-9"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowKey(showKey === p.id ? null : p.id)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        {showKey === p.id ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="px-4 py-3 border-t border-border bg-muted/30 flex justify-end">
                        <Button onClick={handleSave} disabled={loading} size="sm" className="gap-1.5">
                            {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                            Save
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
};
