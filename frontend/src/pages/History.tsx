import React from 'react';
import { Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export const HistoryPage: React.FC = () => {
    return (
        <div className="h-full overflow-auto">
            <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-xl font-semibold text-foreground">History</h1>
                    <p className="text-sm text-muted-foreground mt-0.5">
                        Your previous problem-solving sessions
                    </p>
                </div>

                {/* Empty state */}
                <div className="border border-dashed border-border rounded-lg p-12 flex flex-col items-center justify-center text-center bg-card">
                    <Clock className="h-8 w-8 text-muted-foreground/30 mb-4" />
                    <h3 className="text-sm font-medium text-foreground mb-1">No history yet</h3>
                    <p className="text-xs text-muted-foreground mb-6 max-w-sm">
                        Solve a math problem or analyze a paper to see it here
                    </p>
                    <Link to="/">
                        <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                            Go to Solver <ArrowRight className="h-3 w-3" />
                        </Button>
                    </Link>
                </div>
            </div>
        </div>
    );
};
