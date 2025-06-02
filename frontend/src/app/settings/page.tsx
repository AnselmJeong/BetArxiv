'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function SettingsPage() {
  const [llmProvider, setLlmProvider] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [displayMode, setDisplayMode] = useState('light');
  const [rootDirectory, setRootDirectory] = useState('');

  const handleSaveSettings = () => {
    // TODO: Implement save functionality
    console.log('Saving settings:', {
      llmProvider,
      apiKey,
      displayMode,
      rootDirectory,
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>
      
      <div className="space-y-8">
        {/* LLM Provider Section */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">LLM Provider</h2>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Select LLM Provider
            </label>
            <Select value={llmProvider} onValueChange={setLlmProvider}>
              <SelectTrigger className="max-w-md">
                <SelectValue placeholder="Choose a provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
                <SelectItem value="google">Google</SelectItem>
                <SelectItem value="local">Local Model</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* API Connection Section */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">API Connection</h2>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              API Key
            </label>
            <Input
              type="password"
              placeholder="Enter your API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="max-w-md"
            />
          </div>
        </div>

        {/* Display Preferences Section */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Display Preferences</h2>
          
          <div className="flex space-x-2">
            <Button
              variant={displayMode === 'light' ? 'default' : 'outline'}
              onClick={() => setDisplayMode('light')}
              className="px-6"
            >
              Light Mode
            </Button>
            <Button
              variant={displayMode === 'dark' ? 'default' : 'outline'}
              onClick={() => setDisplayMode('dark')}
              className="px-6"
            >
              Dark Mode
            </Button>
          </div>
        </div>

        {/* Root Directory Section */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Root Directory</h2>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Root Directory
            </label>
            <Input
              type="text"
              placeholder="Enter root directory path"
              value={rootDirectory}
              onChange={(e) => setRootDirectory(e.target.value)}
              className="max-w-md"
            />
          </div>
        </div>

        {/* Save Button */}
        <div className="pt-6">
          <Button onClick={handleSaveSettings} className="px-8">
            Save Settings
          </Button>
        </div>
      </div>
    </div>
  );
} 