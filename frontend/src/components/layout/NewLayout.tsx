/**
 * Unified Layout Component
 * - Professional dark theme
 * - Collapsible sidebar with clear active states
 * - Top bar with environment badge
 * - Proper spacing and accessibility
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Download,
  Brain,
  LineChart,
  TrendingUp,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Search,
  Bell,
  Settings,
  User,
  Activity,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface LayoutProps {
  children: React.ReactNode;
}

interface MenuItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const menuItems: MenuItem[] = [
  { path: '/', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { path: '/download', label: 'Download Data', icon: <Download className="w-5 h-5" /> },
  { path: '/training', label: 'Train Models', icon: <Brain className="w-5 h-5" /> },
  { path: '/analysis', label: 'AI Analysis', icon: <Activity className="w-5 h-5" /> },
  { path: '/backtest', label: 'Backtest', icon: <TrendingUp className="w-5 h-5" /> },
  { path: '/advanced-chart', label: 'Advanced Chart', icon: <LineChart className="w-5 h-5" /> },
  { path: '/portfolio', label: 'Portfolio', icon: <Briefcase className="w-5 h-5" /> },
];

export default function NewLayout({ children }: LayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col border-r bg-card transition-all duration-300',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo / Brand */}
        <div className="flex h-16 items-center justify-between border-b px-4">
          {!collapsed && (
            <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-pink-500 bg-clip-text text-transparent">
              Sigma Analyst
            </h1>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="ml-auto"
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-2">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={cn(
                  'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <span className={cn(isActive && 'text-primary-foreground')}>
                  {item.icon}
                </span>
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        {!collapsed && (
          <div className="border-t p-4">
            <div className="text-xs text-muted-foreground">
              Advanced AI Platform v3.0
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="flex h-16 items-center justify-between border-b bg-card px-6">
          <div className="flex items-center gap-4">
            {/* Breadcrumb / Page Title */}
            <div className="text-sm text-muted-foreground">
              {menuItems.find((item) => item.path === location.pathname)?.label || 'Dashboard'}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Environment Badge */}
            <Badge variant="success" className="gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              LIVE
            </Badge>

            {/* Search */}
            <Button variant="ghost" size="icon">
              <Search className="w-4 h-4" />
            </Button>

            {/* Notifications */}
            <Button variant="ghost" size="icon">
              <Bell className="w-4 h-4" />
            </Button>

            {/* Settings */}
            <Button variant="ghost" size="icon">
              <Settings className="w-4 h-4" />
            </Button>

            {/* User Menu */}
            <Button variant="ghost" size="icon">
              <User className="w-4 h-4" />
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
