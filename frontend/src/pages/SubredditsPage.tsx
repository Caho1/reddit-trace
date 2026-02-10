import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { formatDateTime } from '../lib/format'
import { getErrorMessage } from '../lib/errors'
import {
  createSourceTarget,
  deleteSourceTarget,
  listSourceTargets,
  updateSourceTarget,
  type SourceTarget,
} from '../services/traceHubApi'

const SOURCE_LABEL: Record<string, string> = {
  reddit: 'Reddit',
  hackernews: 'Hacker News',
}

function getSourceLabel(source: string): string {
  return SOURCE_LABEL[source] ?? source
}

const SOURCE_OPTIONS = [
  { value: 'reddit', label: 'Reddit' },
  { value: 'hackernews', label: 'Hacker News' },
]

const TARGET_TYPES: Record<string, Array<{ value: string; label: string }>> = {
  reddit: [
    { value: 'subreddit', label: 'Subreddit' },
    { value: 'post_url', label: 'Post URL' },
  ],
  hackernews: [
    { value: 'feed', label: 'Feed' },
    { value: 'story', label: 'Story ID' },
  ],
}

export function SubredditsPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<SourceTarget | null>(null)

  const [formSource, setFormSource] = useState('reddit')
  const [formTargetType, setFormTargetType] = useState('subreddit')
  const [formTargetKey, setFormTargetKey] = useState('')
  const [formDisplayName, setFormDisplayName] = useState('')
  const [formDesc, setFormDesc] = useState('')
  const [formEnabled, setFormEnabled] = useState(true)
  const [formInterval, setFormInterval] = useState('60')

  const targetsQuery = useQuery({ queryKey: ['source-targets'], queryFn: () => listSourceTargets() })

  const createMutation = useMutation({
    mutationFn: createSourceTarget,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['source-targets'] })
      setModalOpen(false)
      setError(null)
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const updateMutation = useMutation({
    mutationFn: (args: { id: number; payload: Parameters<typeof updateSourceTarget>[1] }) =>
      updateSourceTarget(args.id, args.payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['source-targets'] })
      setModalOpen(false)
      setError(null)
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteSourceTarget,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['source-targets'] })
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const resetForm = () => {
    setFormSource('reddit')
    setFormTargetType('subreddit')
    setFormTargetKey('')
    setFormDisplayName('')
    setFormDesc('')
    setFormEnabled(true)
    setFormInterval('60')
  }

  const openCreate = () => {
    setEditing(null)
    resetForm()
    setModalOpen(true)
  }

  const openEdit = (target: SourceTarget) => {
    setEditing(target)
    setFormSource(target.source)
    setFormTargetType(target.target_type)
    setFormTargetKey(target.target_key)
    setFormDisplayName(target.display_name || '')
    setFormDesc(target.description || '')
    setFormEnabled(target.monitor_enabled)
    setFormInterval(String(target.fetch_interval))
    setModalOpen(true)
  }

  const handleSubmit = () => {
    if (editing) {
      updateMutation.mutate({
        id: editing.id,
        payload: {
          display_name: formDisplayName || formTargetKey,
          description: formDesc,
          monitor_enabled: formEnabled,
          fetch_interval: parseInt(formInterval) || 60,
        },
      })
      return
    }

    if (!formTargetKey.trim()) return
    createMutation.mutate({
      source: formSource,
      target_type: formTargetType,
      target_key: formTargetKey.trim(),
      display_name: (formDisplayName || formTargetKey).trim(),
      description: formDesc,
      monitor_enabled: formEnabled,
      fetch_interval: parseInt(formInterval) || 60,
      options: {
        limit: 50,
        include_comments: false,
        comment_limit: 20,
      },
    })
  }

  const targetTypeOptions = TARGET_TYPES[formSource] || []

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>监控目标</CardTitle>
        <Button onClick={openCreate}>
          <Plus className="w-4 h-4 mr-1" />
          添加
        </Button>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-20">来源</TableHead>
              <TableHead className="w-24">类型</TableHead>
              <TableHead>目标</TableHead>
              <TableHead>描述</TableHead>
              <TableHead className="w-20">监控</TableHead>
              <TableHead className="w-28">间隔(分钟)</TableHead>
              <TableHead className="w-36">上次抓取</TableHead>
              <TableHead className="w-40">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(targetsQuery.data ?? []).map((target) => (
              <TableRow key={target.id}>
                <TableCell className="font-medium">{getSourceLabel(target.source)}</TableCell>
                <TableCell>{target.target_type}</TableCell>
                <TableCell className="truncate max-w-[220px]">
                  {target.display_name || target.target_key}
                </TableCell>
                <TableCell className="text-muted-foreground truncate max-w-[220px]">
                  {target.description || '-'}
                </TableCell>
                <TableCell>
                  <Switch
                    checked={target.monitor_enabled}
                    onCheckedChange={(checked) =>
                      updateMutation.mutate({
                        id: target.id,
                        payload: { monitor_enabled: checked },
                      })
                    }
                  />
                </TableCell>
                <TableCell>{target.fetch_interval}</TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatDateTime(target.last_fetched_at)}
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => openEdit(target)}>
                      编辑
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="destructive" size="sm">
                          删除
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>确定删除？</AlertDialogTitle>
                          <AlertDialogDescription>
                            删除目标 "{target.display_name || target.target_key}" 后无法恢复。
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>取消</AlertDialogCancel>
                          <AlertDialogAction onClick={() => deleteMutation.mutate(target.id)}>
                            删除
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? `编辑：${editing.display_name || editing.target_key}` : '添加监控目标'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {!editing && (
              <>
                <div className="space-y-2">
                  <Label>来源</Label>
                  <select
                    className="w-full border rounded-md px-3 py-2 bg-background"
                    value={formSource}
                    onChange={(e) => {
                      const next = e.target.value
                      setFormSource(next)
                      setFormTargetType((TARGET_TYPES[next] || [])[0]?.value || '')
                    }}
                  >
                    {SOURCE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label>目标类型</Label>
                  <select
                    className="w-full border rounded-md px-3 py-2 bg-background"
                    value={formTargetType}
                    onChange={(e) => setFormTargetType(e.target.value)}
                  >
                    {targetTypeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label>目标键</Label>
                  <Input
                    placeholder={
                      formSource === 'reddit'
                        ? formTargetType === 'subreddit'
                          ? '例如：SaaS'
                          : '例如：https://www.reddit.com/r/.../comments/...'
                        : formTargetType === 'feed'
                          ? '例如：topstories'
                          : '例如：8863'
                    }
                    value={formTargetKey}
                    onChange={(e) => setFormTargetKey(e.target.value)}
                  />
                </div>
              </>
            )}

            <div className="space-y-2">
              <Label>显示名称</Label>
              <Input
                placeholder="可选，不填则使用目标键"
                value={formDisplayName}
                onChange={(e) => setFormDisplayName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>描述</Label>
              <Textarea placeholder="可选" value={formDesc} onChange={(e) => setFormDesc(e.target.value)} />
            </div>

            <div className="flex items-center gap-2">
              <Switch checked={formEnabled} onCheckedChange={setFormEnabled} />
              <Label>开启监控</Label>
            </div>

            <div className="space-y-2">
              <Label>抓取间隔（分钟）</Label>
              <Input
                type="number"
                value={formInterval}
                onChange={(e) => setFormInterval(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
              {editing ? '保存' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
