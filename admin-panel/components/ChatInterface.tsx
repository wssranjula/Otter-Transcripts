'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, User, AlertCircle, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { sendChatMessage, type ChatResponse } from '@/lib/api';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Image from 'next/image';


interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const STORAGE_KEY = 'sybil-chat-history';
const MAX_STORED_MESSAGES = 50; // Store more, but we can display last N

export function ChatInterface() {
  // Load messages from localStorage on mount
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed) && parsed.length > 0) {
            return parsed;
          }
        }
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }
    // Default welcome message
    return [
      {
        role: 'assistant',
        content: '🌍 Hello! I\'m Sybil, Climate Hub\'s AI assistant. I can help you find information about our meetings, environmental initiatives, policy decisions, and team activities. What would you like to know?',
        timestamp: new Date().toISOString(),
      }
    ];
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && messages.length > 0) {
      try {
        // Keep only the last MAX_STORED_MESSAGES
        const toStore = messages.slice(-MAX_STORED_MESSAGES);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
      } catch (e) {
        console.error('Failed to save chat history:', e);
      }
    }
  }, [messages]);

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
      // Send last 10 messages as history (excluding the current user message we just added)
      const historyToSend = messages.slice(-10);
      
      const response = await sendChatMessage(input, historyToSend);

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

  const handleResetChat = () => {
    if (confirm('Are you sure you want to clear the chat history? This cannot be undone.')) {
      // Clear localStorage
      localStorage.removeItem(STORAGE_KEY);
      
      // Reset to welcome message
      setMessages([
        {
          role: 'assistant',
          content: '🌍 Hello! I\'m Sybil, Climate Hub\'s AI assistant. I can help you find information about our meetings, environmental initiatives, policy decisions, and team activities. What would you like to know?',
          timestamp: new Date().toISOString(),
        }
      ]);
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
      {/* Header with Reset Button */}
      <div className="flex justify-between items-center mb-3 md:mb-4">
        <div>
          <h2 className="text-lg md:text-xl font-bold text-green-800 dark:text-green-200">
            Chat with Sybil
          </h2>
          <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">
            {messages.length - 1} messages in this conversation
          </p>
        </div>
        <Button
          onClick={handleResetChat}
          variant="outline"
          size="sm"
          className="border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950"
        >
          <RotateCcw className="h-4 w-4 mr-1 md:mr-2" />
          <span className="hidden md:inline">Reset Chat</span>
        </Button>
      </div>
      
      {/* Messages Area */}
      <Card className="flex-1 mb-3 md:mb-4 overflow-hidden border-2 border-green-200 dark:border-green-900 shadow-lg">
        <CardContent className="h-full overflow-y-auto p-3 md:p-6 bg-gradient-to-b from-white via-green-50/30 to-teal-50/30 dark:from-gray-900 dark:to-gray-950">
          <div className="space-y-4 md:space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex gap-2 md:gap-3 items-start animate-in slide-in-from-bottom-4 duration-300",
                  message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                )}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center shrink-0 shadow-md",
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-cyan-500'
                      : 'bg-gradient-to-br from-green-600 to-teal-600'
                  )}
                >
                  {message.role === 'user' ? (
                    <User className="h-4 w-4 md:h-5 md:w-5 text-white" />
                  ) : (
                    <div className="relative w-5 h-5 md:w-6 md:h-6">
                      <Image
                        src="/icon.png"
                        alt="Sybil"
                        fill
                        className="object-contain brightness-0 invert"
                        unoptimized
                      />
                    </div>
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  className={cn(
                    "flex flex-col gap-1 max-w-[85%] md:max-w-[75%]",
                    message.role === 'user' ? 'items-end' : 'items-start'
                  )}
                >
                  <div
                    className={cn(
                      "rounded-2xl px-3 py-2 md:px-4 md:py-3 shadow-sm",
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white rounded-tr-sm'
                        : 'bg-white dark:bg-gray-800 border-2 border-green-100 dark:border-green-900 rounded-tl-sm'
                    )}
                  >
                    {message.role === 'assistant' ? (
                      <div className="prose prose-sm md:prose-base prose-green dark:prose-invert max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            // Customize markdown rendering
                            p: ({ children }) => <p className="mb-2 last:mb-0 text-sm md:text-base leading-relaxed">{children}</p>,
                            ul: ({ children }) => <ul className="mb-2 ml-4 list-disc text-sm md:text-base">{children}</ul>,
                            ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal text-sm md:text-base">{children}</ol>,
                            li: ({ children }) => <li className="mb-1">{children}</li>,
                            strong: ({ children }) => <strong className="font-bold text-green-700 dark:text-green-300">{children}</strong>,
                            em: ({ children }) => <em className="italic">{children}</em>,
                            h1: ({ children }) => <h1 className="text-lg md:text-xl font-bold mb-2 text-green-800 dark:text-green-200">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-base md:text-lg font-bold mb-2 text-green-800 dark:text-green-200">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-sm md:text-base font-bold mb-1 text-green-800 dark:text-green-200">{children}</h3>,
                            code: ({ children }) => <code className="bg-green-100 dark:bg-green-900 px-1 py-0.5 rounded text-xs md:text-sm font-mono">{children}</code>,
                            pre: ({ children }) => <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-lg overflow-x-auto mb-2 text-xs md:text-sm">{children}</pre>,
                            blockquote: ({ children }) => <blockquote className="border-l-4 border-green-500 pl-3 italic my-2 text-sm md:text-base">{children}</blockquote>,
                            a: ({ children, href }) => <a href={href} className="text-blue-600 dark:text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">{children}</a>,
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm md:text-base whitespace-pre-wrap leading-relaxed">
                        {message.content}
                      </p>
                    )}
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
              <div className="flex gap-2 md:gap-3 items-start animate-in slide-in-from-bottom-4">
                <div className="w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center shrink-0 bg-gradient-to-br from-green-600 to-teal-600 shadow-md">
                  <div className="relative w-5 h-5 md:w-6 md:h-6">
                    <Image
                      src="/icon.png"
                      alt="Sybil"
                      fill
                      className="object-contain brightness-0 invert"
                      unoptimized
                    />
                  </div>
                </div>
                <div className="bg-white dark:bg-gray-800 border-2 border-green-100 dark:border-green-900 rounded-2xl rounded-tl-sm px-3 py-2 md:px-4 md:py-3 shadow-sm">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-green-600" />
                    <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">Sybil is thinking...</p>
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
        <CardContent className="p-3 md:p-4">
          <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-2 md:gap-3">
            <div className="flex-1 relative">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about climate meetings, policies, initiatives..."
                className="min-h-[56px] md:min-h-[64px] max-h-[150px] md:max-h-[200px] resize-none pr-10 md:pr-12 text-sm md:text-base rounded-xl border-2 border-green-200 focus:border-green-400 dark:border-green-800 dark:focus:border-green-600 transition-colors"
                disabled={isLoading}
              />
              <div className="absolute right-2 md:right-3 top-2 md:top-3 w-4 h-4 md:w-5 md:h-5 opacity-50">
                <Image
                  src="/icon.png"
                  alt="Climate Hub"
                  fill
                  className="object-contain"
                />
              </div>
            </div>
            <Button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="h-[56px] md:h-[64px] px-6 md:px-8 rounded-xl bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white shadow-md transition-all"
              size="lg"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 md:h-5 md:w-5 animate-spin" />
              ) : (
                <>
                  <Send className="h-4 w-4 md:h-5 md:w-5 md:mr-2" />
                  <span className="hidden md:inline">Send</span>
                </>
              )}
            </Button>
          </form>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center hidden md:block">
            Press <kbd className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900 rounded text-xs">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900 rounded text-xs">Shift+Enter</kbd> for new line
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
