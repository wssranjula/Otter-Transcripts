'use client';

import { useState, useEffect } from 'react';
import { Save, Loader2, RefreshCw, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  getPromptConfig,
  updatePromptConfig,
  type PromptConfig,
} from '@/lib/api';

export function PromptEditor() {
  const [config, setConfig] = useState<PromptConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getPromptConfig();
      setConfig(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load prompt configuration');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await updatePromptConfig(config);
      setSuccess('Prompt configuration saved successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save prompt configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const updateField = <K extends keyof PromptConfig>(
    field: K,
    value: PromptConfig[K]
  ) => {
    if (!config) return;
    setConfig({ ...config, [field]: value });
  };

  const buildPreview = (): string => {
    if (!config) return '';

    let preview = '**Tone & Style**:\n\n';
    preview += `- **Tone**: ${config.tone}\n`;

    if (config.use_smart_brevity) {
      preview += '- **Smart Brevity**: Follow Axios-style brevity: short paragraphs (2-4 sentences max), bold labels for sections (e.g., **Why it matters:**, **The big picture:**, **Key takeaways:**), and actionable summaries\n';
    }

    if (config.people_references === 'first_names_internally_roles_cross_team') {
      preview += '- **People References**: Use first names for internal references. Use roles when referring cross-team (e.g., "Policy Lead" or "Director")\n';
    }

    if (config.use_formatting) {
      preview += '- **Formatting**: Use bold and bullets for clarity and structure\n';
    }

    if (!config.use_emojis) {
      preview += '- **Emojis**: Do not use emojis unless explicitly requested by the user\n';
    } else {
      preview += '- **Emojis**: Use emojis when appropriate\n';
    }

    preview += `- **Response Length**: For most responses, use ${config.default_response_length}. `;

    if (config.ask_about_depth) {
      preview += 'Unless asked to generate a strategic draft, project memo, or something determined to be longer. When appropriate, ask how much depth the person is looking for, and give options (a few short action items/bullet points or a comprehensive draft including exec summary, etc.)\n';
    } else {
      preview += 'Adjust length based on query complexity.\n';
    }

    if (!config.tone_adapts_by_user) {
      preview += '- **Tone Adaptation**: Do not adapt tone by user - maintain consistent professional tone for all users\n';
    } else {
      preview += '- **Tone Adaptation**: Adapt tone based on user preferences\n';
    }

    if (config.custom_instructions) {
      preview += `\n**Additional Instructions**:\n${config.custom_instructions}\n`;
    }

    return preview;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading prompt configuration...</span>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="p-8">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">Failed to load prompt configuration.</p>
            <Button onClick={loadConfig} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-green-700 to-teal-700 bg-clip-text text-transparent">
            Sybil Prompt Configuration
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Configure the tone, style, and behavior of the Main Supervisor Sybil agent
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowPreview(!showPreview)}
          >
            <Eye className="h-4 w-4 mr-2" />
            {showPreview ? 'Hide' : 'Show'} Preview
          </Button>
          <Button onClick={loadConfig} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Reload
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {success && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <p className="text-green-800">{success}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Left Column - Configuration */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Tone & Style</CardTitle>
              <CardDescription>
                Configure the overall tone and communication style
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Tone Description
                </label>
                <Input
                  value={config.tone}
                  onChange={(e) => updateField('tone', e.target.value)}
                  placeholder="Calm, confident, professional, and concise"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="use_smart_brevity"
                  checked={config.use_smart_brevity}
                  onChange={(e) => updateField('use_smart_brevity', e.target.checked)}
                  className="w-4 h-4"
                />
                <label htmlFor="use_smart_brevity" className="text-sm font-medium">
                  Use Smart Brevity (Axios-style)
                </label>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="use_formatting"
                  checked={config.use_formatting}
                  onChange={(e) => updateField('use_formatting', e.target.checked)}
                  className="w-4 h-4"
                />
                <label htmlFor="use_formatting" className="text-sm font-medium">
                  Use Formatting (bold, bullets)
                </label>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="use_emojis"
                  checked={config.use_emojis}
                  onChange={(e) => updateField('use_emojis', e.target.checked)}
                  className="w-4 h-4"
                />
                <label htmlFor="use_emojis" className="text-sm font-medium">
                  Allow Emojis
                </label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>People References</CardTitle>
              <CardDescription>
                How to refer to people in responses
              </CardDescription>
            </CardHeader>
            <CardContent>
              <select
                value={config.people_references}
                onChange={(e) => updateField('people_references', e.target.value)}
                className="w-full p-2 border rounded-md"
              >
                <option value="first_names_internally_roles_cross_team">
                  First names internally, roles cross-team
                </option>
                <option value="always_first_names">Always first names</option>
                <option value="always_roles">Always roles</option>
              </select>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Response Length</CardTitle>
              <CardDescription>
                Configure default response length and depth options
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Default Response Length
                </label>
                <Input
                  value={config.default_response_length}
                  onChange={(e) => updateField('default_response_length', e.target.value)}
                  placeholder="3-6 sentences or short bullet lists"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="ask_about_depth"
                  checked={config.ask_about_depth}
                  onChange={(e) => updateField('ask_about_depth', e.target.checked)}
                  className="w-4 h-4"
                />
                <label htmlFor="ask_about_depth" className="text-sm font-medium">
                  Ask about depth for longer content
                </label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tone Adaptation</CardTitle>
              <CardDescription>
                Whether tone should adapt by user
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="tone_adapts_by_user"
                  checked={config.tone_adapts_by_user}
                  onChange={(e) => updateField('tone_adapts_by_user', e.target.checked)}
                  className="w-4 h-4"
                />
                <label htmlFor="tone_adapts_by_user" className="text-sm font-medium">
                  Adapt tone by user
                </label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Custom Instructions</CardTitle>
              <CardDescription>
                Additional custom instructions (optional)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={config.custom_instructions}
                onChange={(e) => updateField('custom_instructions', e.target.value)}
                placeholder="Enter any additional instructions..."
                rows={6}
              />
            </CardContent>
          </Card>

          <div className="flex gap-2">
            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Configuration
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Right Column - Preview */}
        {showPreview && (
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Prompt Preview</CardTitle>
                <CardDescription>
                  How the tone & style section will appear in the prompt
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-md border">
                  <pre className="whitespace-pre-wrap text-sm font-mono">
                    {buildPreview()}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}


