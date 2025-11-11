'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare, Users, LayoutDashboard, Menu, X, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import Image from 'next/image';

export function Navigation() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const links = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/chat', label: 'Chat with Sybil', icon: MessageSquare },
    { href: '/whitelist', label: 'Whitelist', icon: Users },
    { href: '/prompt', label: 'Prompt Config', icon: Settings },
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden w-10 h-10 rounded-lg bg-green-600 text-white flex items-center justify-center shadow-lg"
      >
        {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Navigation Sidebar */}
      <nav className={cn(
        "fixed lg:static inset-y-0 left-0 z-40 w-72 bg-gradient-to-b from-green-50 via-emerald-50 to-teal-50 dark:from-gray-900 dark:to-gray-950 border-r border-green-200 dark:border-gray-800 p-4 lg:p-6 transition-transform duration-300",
        isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}>
      {/* Logo/Header */}
      <div className="mb-6 lg:mb-8 mt-12 lg:mt-0">
        <div className="flex items-center gap-2 lg:gap-3 mb-3">
          <div className="relative w-12 h-12 lg:w-14 lg:h-14 shrink-0 bg-white dark:bg-gray-800 rounded-xl p-2 shadow-lg border-2 border-green-200 dark:border-green-800">
            <Image
              src="/logo.png"
              alt="Climate Hub Logo"
              fill
              className="object-contain p-1"
              priority
              unoptimized
            />
          </div>
          <div>
            <h1 className="text-xl lg:text-2xl font-bold text-gray-900 dark:text-gray-100">
              Sybil Admin
            </h1>
            <p className="text-xs lg:text-sm text-green-700 dark:text-green-400 font-semibold">Climate Hub Portal</p>
          </div>
        </div>
        <div className="h-1 bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500 rounded-full shadow-sm" />
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
              onClick={() => setIsOpen(false)}
              className={cn(
                "flex items-center gap-2 lg:gap-3 px-3 lg:px-4 py-2 lg:py-3 rounded-xl transition-all duration-200 group relative text-sm lg:text-base",
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
      <div className="mt-6 lg:mt-8 p-4 bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-950/30 dark:to-teal-950/30 rounded-xl border-2 border-green-200 dark:border-green-800 shadow-md">
        <div className="flex items-center gap-2 mb-2">
          <div className="relative w-5 h-5 shrink-0 bg-white dark:bg-gray-800 rounded-lg p-0.5 border border-green-200 dark:border-green-700">
            <Image
              src="/icon.png"
              alt="Climate Hub"
              fill
              className="object-contain p-0.5"
              unoptimized
            />
          </div>
          <p className="text-xs font-bold text-green-800 dark:text-green-300">Our Mission</p>
        </div>
        <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed font-medium">
          Empowering climate action through intelligent AI-powered knowledge management
        </p>
      </div>

      {/* Footer */}
      <div className="absolute bottom-4 lg:bottom-6 left-4 lg:left-6 right-4 lg:right-6">
        <div className="bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-950/20 dark:to-teal-950/20 rounded-xl p-3 lg:p-4 border border-green-200 dark:border-green-800">
          <p className="text-xs text-gray-600 dark:text-gray-400">
            Powered by <span className="font-semibold text-green-700 dark:text-green-400">Sybil AI</span>
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            For a sustainable future 🌱
          </p>
        </div>
      </div>
    </nav>
    </>
  );
}
