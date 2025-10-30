'use client';

import { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, Loader2, RefreshCw, Power } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  getWhitelist,
  addToWhitelist,
  updateWhitelist,
  deleteFromWhitelist,
  toggleWhitelistStatus,
  getWhitelistStats,
  type WhitelistEntry,
  type WhitelistStats,
} from '@/lib/api';

export function WhitelistTable() {
  const [entries, setEntries] = useState<WhitelistEntry[]>([]);
  const [stats, setStats] = useState<WhitelistStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showInactive, setShowInactive] = useState(true);

  // Form state
  const [formData, setFormData] = useState({
    phone_number: '',
    name: '',
    notes: '',
  });

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [entriesData, statsData] = await Promise.all([
        getWhitelist(showInactive),
        getWhitelistStats(),
      ]);
      setEntries(entriesData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [showInactive]);

  const handleAdd = async () => {
    if (!formData.phone_number.trim()) {
      alert('Phone number is required');
      return;
    }

    try {
      await addToWhitelist({
        phone_number: formData.phone_number,
        name: formData.name || undefined,
        notes: formData.notes || undefined,
        added_by: 'admin',
      });

      setFormData({ phone_number: '', name: '', notes: '' });
      setShowAddForm(false);
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to add entry');
    }
  };

  const handleUpdate = async (id: number) => {
    try {
      await updateWhitelist(id, {
        name: formData.name || undefined,
        notes: formData.notes || undefined,
      });

      setFormData({ phone_number: '', name: '', notes: '' });
      setEditingId(null);
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update entry');
    }
  };

  const handleToggle = async (id: number) => {
    try {
      await toggleWhitelistStatus(id);
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to toggle status');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to remove this number from the whitelist?')) {
      return;
    }

    try {
      await deleteFromWhitelist(id, false);
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete entry');
    }
  };

  const startEdit = (entry: WhitelistEntry) => {
    setEditingId(entry.id);
    setFormData({
      phone_number: entry.phone_number,
      name: entry.name || '',
      notes: entry.notes || '',
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setFormData({ phone_number: '', name: '', notes: '' });
  };

  if (isLoading && entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-2 hover:shadow-lg transition-shadow">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">Total Numbers</CardDescription>
              <CardTitle className="text-4xl font-bold bg-gradient-to-br from-gray-700 to-gray-900 dark:from-gray-100 dark:to-gray-300 bg-clip-text text-transparent">
                {stats.total}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-2 hover:shadow-lg transition-shadow bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium text-green-700 dark:text-green-300">Active</CardDescription>
              <CardTitle className="text-4xl font-bold text-green-600 dark:text-green-400">
                {stats.active}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-2 hover:shadow-lg transition-shadow">
            <CardHeader className="pb-2">
              <CardDescription className="text-sm font-medium">Inactive</CardDescription>
              <CardTitle className="text-4xl font-bold text-gray-500 dark:text-gray-400">
                {stats.inactive}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Manage Numbers</h2>
        <div className="flex gap-2">
          <Button 
            variant={showInactive ? "default" : "outline"} 
            size="sm" 
            onClick={() => setShowInactive(!showInactive)}
            className={showInactive ? "bg-gradient-to-r from-blue-500 to-cyan-500" : ""}
          >
            {showInactive ? 'Hide Inactive' : 'Show Inactive'}
          </Button>
          <Button variant="outline" size="sm" onClick={loadData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button 
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 shadow-md"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Number
          </Button>
        </div>
      </div>

      {error && (
        <Card className="bg-destructive/10 border-destructive">
          <CardContent className="pt-6">
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Add Form */}
      {showAddForm && (
        <Card className="border-2 shadow-lg animate-in slide-in-from-top-4 duration-300">
          <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20">
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-green-600" />
              Add New Number
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            <div>
              <label className="text-sm font-medium">Phone Number *</label>
              <Input
                placeholder="+1234567890"
                value={formData.phone_number}
                onChange={(e) =>
                  setFormData({ ...formData, phone_number: e.target.value })
                }
              />
            </div>
            <div>
              <label className="text-sm font-medium">Name</label>
              <Input
                placeholder="Contact name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </div>
            <div>
              <label className="text-sm font-medium">Notes</label>
              <Textarea
                placeholder="Additional notes..."
                value={formData.notes}
                onChange={(e) =>
                  setFormData({ ...formData, notes: e.target.value })
                }
              />
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={handleAdd}
                className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add to Whitelist
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowAddForm(false);
                  setFormData({ phone_number: '', name: '', notes: '' });
                }}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Entries Table */}
      <Card className="border-2">
        <CardContent className="pt-6">
          <div className="space-y-4">
            {entries.map((entry) => (
              <Card 
                key={entry.id}
                className="hover:shadow-md transition-shadow border-2 animate-in fade-in duration-300"
              >
                <CardContent className="pt-6">
                  {editingId === entry.id ? (
                    // Edit Mode
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">
                          Phone Number
                        </label>
                        <Input
                          value={formData.phone_number}
                          disabled
                          className="bg-muted"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Name</label>
                        <Input
                          value={formData.name}
                          onChange={(e) =>
                            setFormData({ ...formData, name: e.target.value })
                          }
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Notes</label>
                        <Textarea
                          value={formData.notes}
                          onChange={(e) =>
                            setFormData({ ...formData, notes: e.target.value })
                          }
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button onClick={() => handleUpdate(entry.id)}>
                          Save
                        </Button>
                        <Button variant="outline" onClick={cancelEdit}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    // View Mode
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-lg">
                            {entry.phone_number}
                          </h3>
                          <Badge
                            className={
                              entry.is_active 
                                ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white' 
                                : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                            }
                          >
                            {entry.is_active ? '✓ Active' : 'Inactive'}
                          </Badge>
                        </div>
                        {entry.name && (
                          <p className="text-sm text-muted-foreground">
                            {entry.name}
                          </p>
                        )}
                        {entry.notes && (
                          <p className="text-sm mt-2">{entry.notes}</p>
                        )}
                        <p className="text-xs text-muted-foreground mt-2">
                          Added: {new Date(entry.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => startEdit(entry)}
                          title="Edit entry"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant={entry.is_active ? "outline" : "default"}
                          size="sm"
                          onClick={() => handleToggle(entry.id)}
                          title={entry.is_active ? "Deactivate" : "Activate"}
                          className={entry.is_active ? "" : "bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"}
                        >
                          <Power className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDelete(entry.id)}
                          title="Delete entry"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}

            {entries.length === 0 && (
              <div className="text-center py-12">
                <p className="text-muted-foreground">
                  No whitelisted numbers yet. Add one to get started.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

