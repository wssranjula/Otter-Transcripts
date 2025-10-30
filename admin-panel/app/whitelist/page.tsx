import { WhitelistTable } from '@/components/WhitelistTable';
import { Shield } from 'lucide-react';

export default function WhitelistPage() {
  return (
    <div className="p-8">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center shadow-lg">
          <Shield className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-700 to-cyan-700 bg-clip-text text-transparent flex items-center gap-2">
            WhatsApp Whitelist
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Manage secure access for your climate action team
          </p>
        </div>
      </div>
      <WhitelistTable />
    </div>
  );
}
