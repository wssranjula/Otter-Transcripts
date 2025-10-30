'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare, Users, LayoutDashboard, Leaf } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Navigation() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/chat', label: 'Chat with Sybil', icon: MessageSquare },
    { href: '/whitelist', label: 'Whitelist', icon: Users },
  ];

  return (
    <nav className="w-72 bg-gradient-to-b from-green-50 via-emerald-50 to-teal-50 dark:from-gray-900 dark:to-gray-950 border-r border-green-200 dark:border-gray-800 min-h-screen p-6">
      {/* Logo/Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-600 to-teal-600 flex items-center justify-center shadow-lg">
            <Leaf className="h-7 w-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-green-700 to-teal-700 bg-clip-text text-transparent">
              Sybil Admin
            </h1>
            <p className="text-sm text-green-700 dark:text-green-400 font-medium">Climate Hub</p>
          </div>
        </div>
        <div className="h-1 bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500 rounded-full" />
      </div>

      {/* Navigation Links */}
      <div className="space-y-2">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative",
                isActive
                  ? 'bg-gradient-to-r from-green-600 to-teal-600 text-white shadow-lg scale-105'
                  : 'hover:bg-green-100 dark:hover:bg-gray-800 hover:scale-102 text-gray-700 dark:text-gray-300'
              )}
            >
              {isActive && (
                <div className="absolute left-0 w-1 h-8 bg-white rounded-r-full" />
              )}
              <Icon className={cn(
                "h-5 w-5 transition-transform group-hover:scale-110",
                isActive && "drop-shadow-md"
              )} />
              <span className="font-medium">{link.label}</span>
              {isActive && (
                <div className="h-2 w-2 ml-auto bg-green-200 rounded-full animate-pulse" />
              )}
            </Link>
          );
        })}
      </div>

      {/* Mission Statement */}
      <div className="mt-8 p-4 bg-white dark:bg-gray-900 rounded-xl border-2 border-green-200 dark:border-green-900 shadow-sm">
        <div className="flex items-center gap-2 mb-2">
          <Leaf className="h-4 w-4 text-green-600" />
          <p className="text-xs font-semibold text-green-700 dark:text-green-400">Our Mission</p>
        </div>
        <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
          Empowering climate action through intelligent knowledge management
        </p>
      </div>

      {/* Footer */}
      <div className="absolute bottom-6 left-6 right-6">
        <div className="bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-950/20 dark:to-teal-950/20 rounded-xl p-4 border border-green-200 dark:border-green-800">
          <p className="text-xs text-gray-600 dark:text-gray-400">
            Powered by <span className="font-semibold text-green-700 dark:text-green-400">Sybil AI</span>
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            For a sustainable future 🌱
          </p>
        </div>
      </div>
    </nav>
  );
}
