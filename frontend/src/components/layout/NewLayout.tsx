/**
 * Unified Layout Component
 * - Professional dark theme
 * - Collapsible sidebar with clear active states
 * - Top bar with environment badge
 * - Proper spacing and accessibility
 */

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Download,
  Brain,
  LineChart,
  TrendingUp,
  Briefcase,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Search,
  Bell,
  Settings,
  User,
  Activity,
  Languages,
  Check,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import type { Language } from '@/lib/i18n';

interface LayoutProps {
  children: React.ReactNode;
}

interface MenuItem {
  path: string;
  labelKey: keyof typeof menuItemLabels;
  icon: React.ReactNode;
}

// Map menu items to translation keys
const menuItemLabels = {
  dashboard: 'dashboard',
  downloadData: 'downloadData',
  trainModels: 'trainModels',
  aiAnalysis: 'aiAnalysis',
  backtest: 'backtest',
  advancedChart: 'advancedChart',
  portfolio: 'portfolio',
  pdfLearning: 'pdfLearning',
} as const;

const menuItems: MenuItem[] = [
  { path: '/', labelKey: 'dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { path: '/download', labelKey: 'downloadData', icon: <Download className="w-5 h-5" /> },
  { path: '/training', labelKey: 'trainModels', icon: <Brain className="w-5 h-5" /> },
  { path: '/analysis', labelKey: 'aiAnalysis', icon: <Activity className="w-5 h-5" /> },
  { path: '/backtest', labelKey: 'backtest', icon: <TrendingUp className="w-5 h-5" /> },
  { path: '/advanced-chart', labelKey: 'advancedChart', icon: <LineChart className="w-5 h-5" /> },
  { path: '/portfolio', labelKey: 'portfolio', icon: <Briefcase className="w-5 h-5" /> },
  { path: '/pdf-learning', labelKey: 'pdfLearning', icon: <BookOpen className="w-5 h-5" /> },
];

export default function NewLayout({ children }: LayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { language, setLanguage, t } = useLanguage();

  // Close settings dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setShowSettings(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
                {!collapsed && <span>{t.nav[item.labelKey]}</span>}
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
              {t.nav[menuItems.find((item) => item.path === location.pathname)?.labelKey || 'dashboard']}
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

            {/* Settings Dropdown */}
            <div className="relative" ref={settingsRef}>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowSettings(!showSettings)}
              >
                <Settings className="w-4 h-4" />
              </Button>

              {showSettings && (
                <div className="absolute right-0 mt-2 w-56 rounded-lg border bg-card shadow-lg z-50">
                  <div className="p-2">
                    <div className="px-3 py-2 text-sm font-medium text-muted-foreground">
                      {t.common.settings}
                    </div>

                    <div className="mt-1 space-y-1">
                      {/* Language Selector */}
                      <div className="px-3 py-2">
                        <div className="flex items-center gap-2 text-sm font-medium mb-2">
                          <Languages className="w-4 h-4" />
                          {t.common.language}
                        </div>

                        <div className="space-y-1">
                          <button
                            onClick={() => {
                              setLanguage('en');
                              setShowSettings(false);
                            }}
                            className={cn(
                              'flex w-full items-center justify-between rounded px-2 py-1.5 text-sm transition-colors',
                              language === 'en'
                                ? 'bg-primary text-primary-foreground'
                                : 'hover:bg-accent hover:text-accent-foreground'
                            )}
                          >
                            <span>English</span>
                            {language === 'en' && <Check className="w-4 h-4" />}
                          </button>

                          <button
                            onClick={() => {
                              setLanguage('tr');
                              setShowSettings(false);
                            }}
                            className={cn(
                              'flex w-full items-center justify-between rounded px-2 py-1.5 text-sm transition-colors',
                              language === 'tr'
                                ? 'bg-primary text-primary-foreground'
                                : 'hover:bg-accent hover:text-accent-foreground'
                            )}
                          >
                            <span>Türkçe</span>
                            {language === 'tr' && <Check className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

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
