'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Leaf, User, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { sendChatMessage, type ChatResponse } from '@/lib/api';
import { cn } from '@/lib/utils';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '🌍 Hello! I\'m Sybil, Climate Hub\'s AI assistant. I can help you find information about our meetings, environmental initiatives, policy decisions, and team activities. What would you like to know?',
      timestamp: new Date().toISOString(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(input);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Messages Area */}
      <Card className="flex-1 mb-4 overflow-hidden border-2 border-green-200 dark:border-green-900 shadow-lg">
        <CardContent className="h-full overflow-y-auto p-6 bg-gradient-to-b from-white via-green-50/30 to-teal-50/30 dark:from-gray-900 dark:to-gray-950">
          <div className="space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex gap-3 items-start animate-in slide-in-from-bottom-4 duration-300",
                  message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                )}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-md",
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-cyan-500'
                      : 'bg-gradient-to-br from-green-600 to-teal-600'
                  )}
                >
                  {message.role === 'user' ? (
                    <User className="h-5 w-5 text-white" />
                  ) : (
                    <Leaf className="h-5 w-5 text-white" />
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  className={cn(
                    "flex flex-col gap-1 max-w-[75%]",
                    message.role === 'user' ? 'items-end' : 'items-start'
                  )}
                >
                  <div
                    className={cn(
                      "rounded-2xl px-4 py-3 shadow-sm",
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white rounded-tr-sm'
                        : 'bg-white dark:bg-gray-800 border-2 border-green-100 dark:border-green-900 rounded-tl-sm'
                    )}
                  >
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">
                      {message.content}
                    </p>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 px-2">
                    {new Date(message.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3 items-start animate-in slide-in-from-bottom-4">
                <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 bg-gradient-to-br from-green-600 to-teal-600 shadow-md">
                  <Leaf className="h-5 w-5 text-white" />
                </div>
                <div className="bg-white dark:bg-gray-800 border-2 border-green-100 dark:border-green-900 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-green-600" />
                    <p className="text-sm text-gray-600 dark:text-gray-400">Sybil is thinking...</p>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="flex justify-center animate-in fade-in duration-300">
                <Card className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                      <AlertCircle className="h-4 w-4" />
                      <p className="text-sm">{error}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </CardContent>
      </Card>

      {/* Input Area */}
      <Card className="border-2 border-green-200 dark:border-green-900 shadow-lg">
        <CardContent className="p-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="flex-1 relative">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about climate meetings, policies, initiatives..."
                className="min-h-[64px] max-h-[200px] resize-none pr-12 text-base rounded-xl border-2 border-green-200 focus:border-green-400 dark:border-green-800 dark:focus:border-green-600 transition-colors"
                disabled={isLoading}
              />
              <Leaf className="absolute right-3 top-3 h-5 w-5 text-green-500 opacity-50" />
            </div>
            <Button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="h-[64px] px-8 rounded-xl bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white shadow-md transition-all"
              size="lg"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <>
                  <Send className="h-5 w-5 mr-2" />
                  <span>Send</span>
                </>
              )}
            </Button>
          </form>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
            Press <kbd className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900 rounded text-xs">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900 rounded text-xs">Shift+Enter</kbd> for new line
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
