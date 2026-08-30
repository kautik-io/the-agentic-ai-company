"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, AiProviderConfig, ProviderModelCatalog } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ErrorBanner } from "@/components/ui/error-banner";
import { Input, Label, Select } from "@/components/ui/input";
import { KeyRound, Loader2, Plus, RefreshCw, Trash2 } from "lucide-react";

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google AI",
};

export function AiProviderSettings() {
  const { org } = useAuth();
  const [configs, setConfigs] = useState<AiProviderConfig[]>([]);
  const [catalog, setCatalog] = useState<ProviderModelCatalog[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchMessage, setFetchMessage] = useState<string | null>(null);
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [modelsFetched, setModelsFetched] = useState(false);

  const load = async () => {
    if (!org) return;
    const [c, cat] = await Promise.all([
      api.listAiProviders(org.id),
      api.getProviderCatalog(org.id),
    ]);
    setConfigs(c);
    setCatalog(cat);
  };

  useEffect(() => {
    load().catch(console.error);
  }, [org]);

  const availableProviders = catalog.filter(
    (c) => !configs.some((x) => x.provider === c.provider)
  );

  const resetFormState = () => {
    setApiKey("");
    setAvailableModels([]);
    setSelectedModels([]);
    setModelsFetched(false);
    setFetchMessage(null);
    setError(null);
  };

  const fetchModels = useCallback(async (): Promise<string[]> => {
    if (!org || apiKey.length < 8) return [];
    setFetchingModels(true);
    setError(null);
    setFetchMessage(null);
    try {
      const result = await api.fetchProviderModels(org.id, provider, apiKey);
      setAvailableModels(result.models);
      setSelectedModels(result.recommended);
      setModelsFetched(true);
      if (result.message) {
        setFetchMessage(result.message);
      }
      return result.recommended;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch models");
      setModelsFetched(false);
      const fallback = catalog.find((c) => c.provider === provider)?.models || [];
      setAvailableModels(fallback);
      const picked = fallback.slice(0, 2);
      setSelectedModels(picked);
      return picked;
    } finally {
      setFetchingModels(false);
    }
  }, [org, provider, apiKey, catalog]);

  // Auto-fetch when API key is pasted (debounced)
  useEffect(() => {
    if (!showForm || apiKey.length < 12) return;
    const timer = setTimeout(() => {
      fetchModels();
    }, 800);
    return () => clearTimeout(timer);
  }, [apiKey, provider, showForm, fetchModels]);

  const toggleModel = (model: string) => {
    setSelectedModels((prev) =>
      prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    let modelsToSave = selectedModels;
    if (!modelsFetched) {
      modelsToSave = await fetchModels();
    }
    if (modelsToSave.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      await api.saveAiProvider(org.id, {
        provider,
        api_key: apiKey,
        enabled_models: modelsToSave,
      });
      setShowForm(false);
      resetFormState();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save provider");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (configId: string) => {
    if (!org || !window.confirm("Remove this API key? Agents using this provider will be hidden.")) return;
    await api.deleteAiProvider(org.id, configId);
    await load();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <KeyRound className="h-5 w-5" />
            AI Provider Keys
          </h2>
          <p className="text-sm text-muted-foreground">
            Paste your API key — models are fetched automatically from the provider.
          </p>
        </div>
        <Button
          onClick={() => {
            setShowForm(!showForm);
            setProvider(availableProviders[0]?.provider || "openai");
            resetFormState();
          }}
          disabled={availableProviders.length === 0 && configs.length >= catalog.length}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Provider Key
        </Button>
      </div>

      {error && <ErrorBanner message={error} />}
      {fetchMessage && !error && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          {fetchMessage}
        </div>
      )}

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add AI Provider</CardTitle>
            <CardDescription>Paste API key → models load automatically from OpenAI / Anthropic / Google</CardDescription>
          </CardHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label>Provider *</Label>
              <Select
                value={provider}
                onChange={(e) => {
                  setProvider(e.target.value);
                  setAvailableModels([]);
                  setSelectedModels([]);
                  setModelsFetched(false);
                }}
              >
                {(availableProviders.length ? availableProviders : catalog).map((c) => (
                  <option key={c.provider} value={c.provider}>{c.label}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>API Key *</Label>
              <div className="flex gap-2">
                <Input
                  type="password"
                  value={apiKey}
                  onChange={(e) => {
                    setApiKey(e.target.value);
                    setModelsFetched(false);
                  }}
                  placeholder="sk-... or sk-ant-..."
                  required
                  minLength={8}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={fetchModels}
                  disabled={fetchingModels || apiKey.length < 8}
                >
                  {fetchingModels ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  <span className="ml-2 hidden sm:inline">Fetch Models</span>
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Models auto-fetch after you paste your key
              </p>
            </div>
            <div>
              <Label>
                Enabled models *
                {fetchingModels && (
                  <span className="ml-2 text-muted-foreground font-normal">Fetching from {PROVIDER_LABELS[provider]}...</span>
                )}
                {modelsFetched && !fetchingModels && (
                  <span className="ml-2 text-primary font-normal">{availableModels.length} models found</span>
                )}
              </Label>
              {!modelsFetched && !fetchingModels && availableModels.length === 0 ? (
                <p className="text-sm text-muted-foreground mt-2 py-4 text-center border border-dashed border-border rounded-lg">
                  Paste your API key above to load available models
                </p>
              ) : (
                <div className="mt-2 max-h-48 overflow-y-auto grid sm:grid-cols-2 gap-2 border border-border rounded-lg p-3">
                  {availableModels.map((model) => (
                    <label key={model} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedModels.includes(model)}
                        onChange={() => toggleModel(model)}
                      />
                      <span className="truncate" title={model}>{model}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={loading || fetchingModels || selectedModels.length === 0}>
                {loading ? "Saving..." : "Save Provider"}
              </Button>
              <Button type="button" variant="outline" onClick={() => { setShowForm(false); resetFormState(); }}>
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {configs.length === 0 ? (
        <Card className="text-center py-8 text-muted-foreground">
          No API keys configured. Add OpenAI, Anthropic, or Google keys to enable AI employees.
        </Card>
      ) : (
        configs.map((c) => (
          <Card key={c.id}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold">{PROVIDER_LABELS[c.provider] || c.provider}</h3>
                <p className="text-sm text-muted-foreground font-mono mt-1">Key: {c.api_key_masked}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {c.enabled_models.map((m) => (
                    <span key={m} className="text-xs rounded bg-primary/10 text-primary px-2 py-0.5">{m}</span>
                  ))}
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={() => handleDelete(c.id)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </Card>
        ))
      )}
    </div>
  );
}
