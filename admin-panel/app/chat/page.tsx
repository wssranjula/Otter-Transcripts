import { ChatInterface } from '@/components/ChatInterface';
import { Leaf, MessageSquare } from 'lucide-react';

export default function ChatPage() {
  return (
    <div className="p-8 h-full flex flex-col">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-600 to-teal-600 flex items-center justify-center shadow-lg">
          <Leaf className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-700 to-teal-700 bg-clip-text text-transparent flex items-center gap-2">
            Chat with Sybil
            <MessageSquare className="h-6 w-6 text-green-600" />
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
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
