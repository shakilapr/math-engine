export interface PatchHunk {
    kind: 'add' | 'update' | 'delete';
    path: string;
    old_text?: string;
    new_text?: string;
    content?: string;
}

export interface ImprovementProposal {
    analysis: string;
    files: string[];
    hunks: PatchHunk[];
    confidence: string;
}

export interface HistoryEntry {
    backup_id: string;
    timestamp: number;
    operation: string;
    files: string[];
    description: string;
}

export interface ImproveRequest {
    problem_latex: string;
    category?: string;
    error: string;
    code: string;
    traceback?: string;
}
