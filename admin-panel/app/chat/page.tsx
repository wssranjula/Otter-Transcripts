import { ChatInterface } from '@/components/ChatInterface';
import { Leaf, MessageSquare } from 'lucide-react';

export default function ChatPage() {
  return (
    <div className="p-4 md:p-6 lg:p-8 h-full flex flex-col pt-16 lg:pt-8">
      <div className="flex items-center gap-3 md:gap-4 mb-4 md:mb-6">
        <div className="w-12 h-12 md:w-14 md:h-14 rounded-xl md:rounded-2xl bg-gradient-to-br from-green-600 to-teal-600 flex items-center justify-center shadow-lg shrink-0">
          <Leaf className="h-6 w-6 md:h-8 md:w-8 text-white" />
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
