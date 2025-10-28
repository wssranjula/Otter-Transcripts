'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { whitelistApi } from '@/lib/api'
import { WhitelistResponse, PhoneNumber } from '@/lib/types'
import { toast } from 'sonner'
import { Plus, Trash2, Shield, Users, X } from 'lucide-react'

export default function WhitelistPage() {
  const [whitelist, setWhitelist] = useState<WhitelistResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAdding, setIsAdding] = useState(false)
  const [newPhone, setNewPhone] = useState('')
  const [newName, setNewName] = useState('')
  const [isToggling, setIsToggling] = useState(false)

  useEffect(() => {
    const fetchWhitelist = async () => {
      try {
        const data = await whitelistApi.getWhitelist()
        setWhitelist(data)
      } catch (error) {
        console.error('Failed to fetch whitelist:', error)
        toast.error('Failed to load whitelist')
      } finally {
        setIsLoading(false)
      }
    }

    fetchWhitelist()
  }, [])

  const handleAddPhone = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPhone.trim()) return

    setIsAdding(true)
    try {
      await whitelistApi.addToWhitelist(newPhone.trim(), newName.trim() || undefined)
      toast.success('Phone number added to whitelist')
      setNewPhone('')
      setNewName('')
      // Refresh the list
      const data = await whitelistApi.getWhitelist()
      setWhitelist(data)
    } catch (error: any) {
      console.error('Failed to add phone:', error)
      toast.error(error.response?.data?.detail || 'Failed to add phone number')
    } finally {
      setIsAdding(false)
    }
  }

  const handleRemovePhone = async (phoneNumber: string) => {
    try {
      await whitelistApi.removeFromWhitelist(phoneNumber)
      toast.success('Phone number removed from whitelist')
      // Refresh the list
      const data = await whitelistApi.getWhitelist()
      setWhitelist(data)
    } catch (error: any) {
      console.error('Failed to remove phone:', error)
      toast.error(error.response?.data?.detail || 'Failed to remove phone number')
    }
  }

  const handleToggleWhitelist = async () => {
    if (!whitelist) return

    setIsToggling(true)
    try {
      await whitelistApi.toggleWhitelist(!whitelist.enabled)
      toast.success(`Whitelist ${!whitelist.enabled ? 'enabled' : 'disabled'}`)
      // Refresh the list
      const data = await whitelistApi.getWhitelist()
      setWhitelist(data)
    } catch (error: any) {
      console.error('Failed to toggle whitelist:', error)
      toast.error(error.response?.data?.detail || 'Failed to toggle whitelist')
    } finally {
      setIsToggling(false)
    }
  }

  const formatPhoneNumber = (phone: string) => {
    // Basic E.164 formatting
    if (phone.startsWith('+')) return phone
    return `+${phone}`
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Whitelist Management</h1>
          <p className="mt-2 text-gray-600">
            Manage authorized WhatsApp phone numbers
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Loading...</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Loading...</CardTitle>
            </CardHeader>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Whitelist Management</h1>
          <p className="mt-2 text-gray-600">
            Manage authorized WhatsApp phone numbers
          </p>
        </div>
        <Button
          onClick={handleToggleWhitelist}
          disabled={isToggling}
          variant={whitelist?.enabled ? 'destructive' : 'default'}
        >
          <Shield className="w-4 h-4 mr-2" />
          {isToggling ? 'Toggling...' : whitelist?.enabled ? 'Disable Whitelist' : 'Enable Whitelist'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Add Phone Number */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Plus className="w-5 h-5 mr-2" />
              Add Phone Number
            </CardTitle>
            <CardDescription>
              Add a new phone number to the whitelist
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddPhone} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  placeholder="+1234567890"
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Use E.164 format (e.g., +1234567890)
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Name (Optional)</Label>
                <Input
                  id="name"
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="John Doe"
                />
              </div>
              <Button type="submit" disabled={isAdding} className="w-full">
                {isAdding ? 'Adding...' : 'Add to Whitelist'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Whitelist Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="w-5 h-5 mr-2" />
              Whitelist Status
            </CardTitle>
            <CardDescription>
              Current whitelist configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                whitelist?.enabled 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {whitelist?.enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Authorized Numbers</span>
              <span className="text-sm font-bold">
                {whitelist?.authorized_numbers.length || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Blocked Numbers</span>
              <span className="text-sm font-bold">
                {whitelist?.blocked_numbers.length || 0}
              </span>
            </div>
            {whitelist?.unauthorized_message && (
              <div>
                <span className="text-sm font-medium">Unauthorized Message</span>
                <p className="text-sm text-muted-foreground mt-1">
                  {whitelist.unauthorized_message}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Authorized Numbers List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Authorized Numbers
          </CardTitle>
          <CardDescription>
            Phone numbers that can chat with the WhatsApp bot
          </CardDescription>
        </CardHeader>
        <CardContent>
          {whitelist?.authorized_numbers && whitelist.authorized_numbers.length > 0 ? (
            <div className="space-y-2">
              {whitelist.authorized_numbers.map((phone, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <div className="font-medium">{formatPhoneNumber(phone.phone_number)}</div>
                    {phone.name && (
                      <div className="text-sm text-muted-foreground">{phone.name}</div>
                    )}
                    <div className="text-xs text-muted-foreground">
                      Added: {phone.added_at}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemovePhone(phone.phone_number)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No authorized numbers yet</p>
              <p className="text-sm">Add phone numbers above to get started</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
