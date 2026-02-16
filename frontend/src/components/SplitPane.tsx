import React, { useState, useRef, useCallback, useEffect } from 'react';

interface SplitPaneProps {
    left: React.ReactNode;
    right: React.ReactNode;
    defaultSplit?: number; // percentage 0-100
    minLeft?: number; // px
    minRight?: number; // px
    rightCollapsed?: boolean;
}

export const SplitPane: React.FC<SplitPaneProps> = ({
    left,
    right,
    defaultSplit = 60,
    minLeft = 300,
    minRight = 280,
    rightCollapsed = false,
}) => {
    const [splitPercent, setSplitPercent] = useState(defaultSplit);
    const containerRef = useRef<HTMLDivElement>(null);
    const isDragging = useRef(false);

    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        isDragging.current = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    }, []);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isDragging.current || !containerRef.current) return;
            const rect = containerRef.current.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const totalWidth = rect.width;
            let percent = (x / totalWidth) * 100;

            // Enforce minimums
            const minLeftPercent = (minLeft / totalWidth) * 100;
            const minRightPercent = (minRight / totalWidth) * 100;
            percent = Math.max(minLeftPercent, Math.min(100 - minRightPercent, percent));

            setSplitPercent(percent);
        };

        const handleMouseUp = () => {
            if (isDragging.current) {
                isDragging.current = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [minLeft, minRight]);

    return (
        <div ref={containerRef} className="flex h-full w-full overflow-hidden">
            {/* Left panel */}
            <div
                className="h-full overflow-hidden flex flex-col"
                style={{ width: rightCollapsed ? '100%' : `${splitPercent}%` }}
            >
                {left}
            </div>

            {/* Divider */}
            {!rightCollapsed && (
                <div
                    onMouseDown={handleMouseDown}
                    className="w-1 bg-border hover:bg-primary/40 cursor-col-resize transition-colors flex-shrink-0 relative group"
                >
                    <div className="absolute inset-y-0 -left-1 -right-1 z-10" />
                    <div className="absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 w-1 h-8 rounded-full bg-muted-foreground/30 group-hover:bg-primary/60 transition-colors" />
                </div>
            )}

            {/* Right panel */}
            {!rightCollapsed && (
                <div
                    className="h-full overflow-hidden flex flex-col"
                    style={{ width: `${100 - splitPercent}%` }}
                >
                    {right}
                </div>
            )}
        </div>
    );
};
