import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare, Users, Activity, TrendingUp, Wind, Droplet } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import Image from 'next/image';

export default function DashboardPage() {
  // Mock data - in real app, fetch from API
  const stats = {
    totalChats: 0,
    activeUsers: 0,
    whitelistedNumbers: 0,
    responseTime: '< 2s',
  };

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-6 md:space-y-8 pt-16 lg:pt-8">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 md:gap-4">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-green-700 to-teal-700 bg-clip-text text-transparent mb-1 md:mb-2 truncate">
            Climate Hub Admin Portal
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base lg:text-lg">
            Empowering climate action through AI-powered knowledge management
          </p>
        </div>
        <div className="relative w-16 h-16 md:w-20 md:h-20 lg:w-24 lg:h-24 shrink-0 bg-white dark:bg-gray-800 rounded-2xl p-3 shadow-xl border-2 border-green-200 dark:border-green-700 animate-pulse">
          <Image
            src="/logo.png"
            alt="Climate Hub Logo"
            fill
            className="object-contain p-2"
            priority
            unoptimized
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-2 border-blue-200 hover:shadow-lg transition-shadow bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Total Chats
            </CardTitle>
            <MessageSquare className="h-5 w-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-700">{stats.totalChats}</div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Start chatting to see stats
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-green-200 hover:shadow-lg transition-shadow bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Whitelisted Numbers
            </CardTitle>
            <Users className="h-5 w-5 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-700">{stats.whitelistedNumbers}</div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Authorized WhatsApp users
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-orange-200 hover:shadow-lg transition-shadow bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950/20 dark:to-amber-950/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Active Users
            </CardTitle>
            <Activity className="h-5 w-5 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-700">{stats.activeUsers}</div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Last 24 hours
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-teal-200 hover:shadow-lg transition-shadow bg-gradient-to-br from-teal-50 to-cyan-50 dark:from-teal-950/20 dark:to-cyan-950/20">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Avg Response Time
            </CardTitle>
            <TrendingUp className="h-5 w-5 text-teal-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-teal-700">{stats.responseTime}</div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              Lightning fast ⚡
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-2 border-green-200 hover:border-green-400 transition-colors bg-white dark:bg-gray-900">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-600 to-emerald-600 flex items-center justify-center shadow-md">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
              <div>
                <CardTitle>Chat with Sybil</CardTitle>
                <CardDescription>
                  Ask questions about meetings, decisions, and climate initiatives
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Link href="/chat">
              <Button className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white shadow-md">
                <MessageSquare className="h-4 w-4 mr-2" />
                Start Chatting
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="border-2 border-blue-200 hover:border-blue-400 transition-colors bg-white dark:bg-gray-900">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-md">
                <Users className="h-6 w-6 text-white" />
              </div>
              <div>
                <CardTitle>Manage Whitelist</CardTitle>
                <CardDescription>
                  Control which WhatsApp numbers can access the bot
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Link href="/whitelist">
              <Button className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white shadow-md">
                <Users className="h-4 w-4 mr-2" />
                Manage Whitelist
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="border-2 border-purple-200 hover:border-purple-400 transition-colors bg-white dark:bg-gray-900">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center shadow-md">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
              <div>
                <CardTitle>Configure Prompt</CardTitle>
                <CardDescription>
                  Set tone, style, and behavior for Sybil supervisor agent
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Link href="/prompt">
              <Button className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-md">
                <MessageSquare className="h-4 w-4 mr-2" />
                Configure Prompt
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Climate Action Features */}
      <Card className="border-2 border-green-200 bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-950/20 dark:to-teal-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="relative w-5 h-5 shrink-0">
              <Image
                src="/icon.png"
                alt="Climate Hub"
                fill
                className="object-contain"
              />
            </div>
            Sybil: Your Climate Intelligence Assistant
          </CardTitle>
          <CardDescription>
            AI-powered knowledge management for environmental action
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="flex gap-3 p-4 bg-white dark:bg-gray-900 rounded-xl border-2 border-blue-100 dark:border-blue-900">
              <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                <Wind className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold mb-1 text-gray-900 dark:text-gray-100">Meeting Insights</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Query climate meetings, UNEA prep calls, and team decisions
                </p>
              </div>
            </div>

            <div className="flex gap-3 p-4 bg-white dark:bg-gray-900 rounded-xl border-2 border-green-100 dark:border-green-900">
              <div className="relative w-10 h-10 shrink-0">
                <Image
                  src="/icon.png"
                  alt="Climate Hub"
                  fill
                  className="object-contain"
                />
              </div>
              <div>
                <h3 className="font-semibold mb-1 text-gray-900 dark:text-gray-100">Policy Tracking</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Track environmental policies, proposals, and action items
                </p>
              </div>
            </div>

            <div className="flex gap-3 p-4 bg-white dark:bg-gray-900 rounded-xl border-2 border-teal-100 dark:border-teal-900">
              <div className="w-10 h-10 rounded-lg bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center shrink-0">
                <Droplet className="h-5 w-5 text-teal-600 dark:text-teal-400" />
              </div>
              <div>
                <h3 className="font-semibold mb-1 text-gray-900 dark:text-gray-100">WhatsApp Access</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Secure team communication with whitelist management
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
