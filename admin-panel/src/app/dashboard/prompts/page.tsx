'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { configApi } from '@/lib/api'
import { PromptSections } from '@/lib/types'
import { toast } from 'sonner'
import { Save, RotateCcw } from 'lucide-react'

const promptSections = [
  {
    id: 'identity',
    title: 'Identity & Purpose', 
    description: 'Core identity, role, and primary objectives of Sybil'
  },
  {
    id: 'objectives',
    title: 'Information Hierarchy',
    description: 'Source priority and how to handle conflicting information'
  },
  {
    id: 'voice_and_tone',
    title: 'Voice & Tone',
    description: 'Communication style and formatting guidelines'
  },
  {
    id: 'privacy_boundaries',
    title: 'Privacy & Boundaries',
    description: 'Confidentiality rules and sensitive content handling'
  },
  {
    id: 'knowledge_management',
    title: 'Knowledge Management',
    description: 'Data freshness and information updating policies'
  },
  {
    id: 'technical_guidance',
    title: 'Technical Guidance',
    description: 'Neo4j schema and query strategies'
  }
]

export default function PromptsPage() {
  const [sections, setSections] = useState<PromptSections>({})
  const [originalSections, setOriginalSections] = useState<PromptSections>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [activeSection, setActiveSection] = useState('identity')

  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        const data = await configApi.getSybilPrompt()
        setSections(data.sections)
        setOriginalSections(data.sections)
      } catch (error) {
        console.error('Failed to fetch prompts:', error)
        toast.error('Failed to load prompts')
      } finally {
        setIsLoading(false)
      }
    }

    fetchPrompts()
  }, [])

  const handleSectionChange = (sectionId: string, content: string) => {
    setSections(prev => ({
      ...prev,
      [sectionId]: content
    }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await configApi.updateSybilPrompt(activeSection, sections[activeSection])
      toast.success('Prompt section saved successfully')
    } catch (error) {
      console.error('Failed to save prompt:', error)
      toast.error('Failed to save prompt section')
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    setSections(prev => ({
      ...prev,
      [activeSection]: originalSections[activeSection]
    }))
    toast.info('Section reset to original')
  }

  const hasChanges = sections[activeSection] !== originalSections[activeSection]

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Prompt Management</h1>
          <p className="mt-2 text-gray-600">
            Edit Sybil agent system prompts
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Loading...</CardTitle>
              </CardHeader>
            </Card>
          </div>
          <div className="lg:col-span-3">
            <Card>
              <CardHeader>
                <CardTitle>Loading...</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-gray-200 rounded animate-pulse" />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Prompt Management</h1>
        <p className="mt-2 text-gray-600">
          Edit Sybil agent system prompts
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Section Navigation */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Prompt Sections</CardTitle>
              <CardDescription>
                Select a section to edit
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {promptSections.map((section) => (
                <Button
                  key={section.id}
                  variant={activeSection === section.id ? 'default' : 'ghost'}
                  className="w-full justify-start text-left h-auto p-3"
                  onClick={() => setActiveSection(section.id)}
                >
                  <div>
                    <div className="font-medium">{section.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {section.description}
                    </div>
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Section Editor */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>
                    {promptSections.find(s => s.id === activeSection)?.title}
                  </CardTitle>
                  <CardDescription>
                    {promptSections.find(s => s.id === activeSection)?.description}
                  </CardDescription>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    onClick={handleReset}
                    disabled={!hasChanges}
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={!hasChanges || isSaving}
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {isSaving ? 'Saving...' : 'Save'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="prompt-content">
                  Prompt Content
                </Label>
                <textarea
                  id="prompt-content"
                  className="w-full h-96 p-3 border border-input rounded-md font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  value={sections[activeSection] || ''}
                  onChange={(e) => handleSectionChange(activeSection, e.target.value)}
                  placeholder="Enter prompt content..."
                />
                {hasChanges && (
                  <p className="text-sm text-amber-600">
                    You have unsaved changes
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
