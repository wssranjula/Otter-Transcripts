import { ChatInterface } from '@/components/ChatInterface';
import { MessageSquare } from 'lucide-react';
import Image from 'next/image';

export default function ChatPage() {
  return (
    <div className="p-4 md:p-6 lg:p-8 h-full flex flex-col pt-16 lg:pt-8">
      <div className="flex items-center gap-3 md:gap-4 mb-4 md:mb-6">
        <div className="relative w-14 h-14 md:w-16 md:h-16 shrink-0 bg-white dark:bg-gray-800 rounded-xl p-2 shadow-lg border-2 border-green-200 dark:border-green-700">
          <Image
            src="/logo.png"
            alt="Climate Hub Logo"
            fill
            className="object-contain p-1"
            priority
            unoptimized
          />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-green-700 to-teal-700 bg-clip-text text-transparent flex items-center gap-2 truncate">
            Chat with Sybil
            <MessageSquare className="h-5 w-5 md:h-6 md:w-6 text-green-600 shrink-0" />
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base lg:text-lg">
            Your AI assistant for climate action knowledge
          </p>
        </div>
      </div>
      <div className="flex-1 flex flex-col min-h-0">
        <ChatInterface />
      </div>
    </div>
  );
}
