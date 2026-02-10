import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Calculator, FileText, Settings, History, Menu, ChevronLeft, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            {/* Sidebar */}
            <aside
                className={cn(
                    "flex flex-col border-r border-border bg-card transition-all duration-200",
                    collapsed ? "w-[60px]" : "w-56"
                )}
            >
                {/* Logo */}
                <div className="flex items-center gap-2.5 px-4 h-14 border-b border-border">
                    <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/10 text-primary">
                        <Calculator className="h-4 w-4" />
                    </div>
                    {!collapsed && (
                        <span className="font-semibold text-sm tracking-tight text-foreground">
                            MathEngine
                        </span>
                    )}
                </div>

                {/* Nav */}
                <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
                    <NavItem to="/" icon={<Calculator />} label="Solver" collapsed={collapsed} />
                    <NavItem to="/papers" icon={<FileText />} label="Papers" collapsed={collapsed} />
                    <NavItem to="/history" icon={<History />} label="History" collapsed={collapsed} />
                    <NavItem to="/evolution" icon={<Zap />} label="Evolution" collapsed={collapsed} />
                    <div className="my-2 border-t border-border mx-1" />
                    <NavItem to="/settings" icon={<Settings />} label="Settings" collapsed={collapsed} />
                </nav>

                {/* Collapse toggle */}
                <div className="p-2 border-t border-border">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setCollapsed(!collapsed)}
                        className="w-full justify-center text-muted-foreground hover:text-foreground h-8"
                    >
                        {collapsed ? <Menu className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
                    </Button>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 overflow-hidden flex flex-col bg-background">
                {children}
            </main>
        </div>
    );
};

const NavItem = ({ to, icon, label, collapsed }: { to: string; icon: React.ReactNode; label: string; collapsed: boolean }) => (
    <NavLink
        to={to}
        className={({ isActive }) => cn(
            "flex items-center gap-2.5 px-2.5 py-2 rounded-md transition-colors text-sm",
            isActive
                ? "bg-accent text-foreground font-medium"
                : "text-muted-foreground hover:text-foreground hover:bg-accent/50",
            collapsed && "justify-center px-0"
        )}
    >
        {React.isValidElement(icon)
            ? React.cloneElement(icon as React.ReactElement<{ className?: string }>, {
                className: cn("h-4 w-4 shrink-0", collapsed ? "h-5 w-5" : "")
            })
            : null}
        {!collapsed && <span>{label}</span>}
    </NavLink>
);
