import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
  createSubreddit,
  deleteSubreddit,
  listSubreddits,
  updateSubreddit,
  type Subreddit,
} from '../services/redditTraceApi'

export function SubredditsPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Subreddit | null>(null)

  // Form states
  const [formName, setFormName] = useState('')
  const [formDesc, setFormDesc] = useState('')
  const [formEnabled, setFormEnabled] = useState(true)
  const [formInterval, setFormInterval] = useState('60')

  const subredditsQuery = useQuery({ queryKey: ['subreddits'], queryFn: listSubreddits })

  const createMutation = useMutation({
    mutationFn: createSubreddit,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['subreddits'] })
      setModalOpen(false)
      setError(null)
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const updateMutation = useMutation({
    mutationFn: (args: { id: number; payload: Parameters<typeof updateSubreddit>[1] }) =>
      updateSubreddit(args.id, args.payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['subreddits'] })
      setModalOpen(false)
      setError(null)
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteSubreddit,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['subreddits'] })
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const openCreate = () => {
    setEditing(null)
    setFormName('')
    setFormDesc('')
    setFormEnabled(true)
    setFormInterval('60')
    setModalOpen(true)
  }

  const openEdit = (s: Subreddit) => {
    setEditing(s)
    setFormName(s.name)
    setFormDesc(s.description ?? '')
    setFormEnabled(s.monitor_enabled)
    setFormInterval(String(s.fetch_interval))
    setModalOpen(true)
  }

  const handleSubmit = () => {
    if (editing) {
      updateMutation.mutate({
        id: editing.id,
        payload: {
          description: formDesc,
          monitor_enabled: formEnabled,
          fetch_interval: parseInt(formInterval) || 60,
        },
      })
    } else {
      if (!formName.trim()) return
      createMutation.mutate({
        name: formName.trim(),
        description: formDesc,
        monitor_enabled: formEnabled,
        fetch_interval: parseInt(formInterval) || 60,
      })
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>监控板块</CardTitle>
        <Button onClick={openCreate}>
          <Plus className="w-4 h-4 mr-1" />
          添加
        </Button>
      </CardHeader>
      <CardContent>
        {error && <div className="mb-4 p-3 bg-destructive/10 text-destructive text-sm">{error}</div>}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>名称</TableHead>
              <TableHead>描述</TableHead>
              <TableHead className="w-20">监控</TableHead>
              <TableHead className="w-28">间隔(分钟)</TableHead>
              <TableHead className="w-36">上次抓取</TableHead>
              <TableHead className="w-40">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(subredditsQuery.data ?? []).map((s) => (
              <TableRow key={s.id}>
                <TableCell className="font-medium">{s.name}</TableCell>
                <TableCell className="text-muted-foreground truncate max-w-[200px]">
                  {s.description || '-'}
                </TableCell>
                <TableCell>
                  <Switch
                    checked={s.monitor_enabled}
                    onCheckedChange={(checked) =>
                      updateMutation.mutate({ id: s.id, payload: { monitor_enabled: checked } })
                    }
                  />
                </TableCell>
                <TableCell>{s.fetch_interval}</TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatDateTime(s.last_fetched_at)}
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => openEdit(s)}>
                      编辑
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="destructive" size="sm">删除</Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>确定删除？</AlertDialogTitle>
                          <AlertDialogDescription>
                            删除板块 "{s.name}" 后无法恢复。
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>取消</AlertDialogCancel>
                          <AlertDialogAction onClick={() => deleteMutation.mutate(s.id)}>
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
            <DialogTitle>{editing ? `编辑：${editing.name}` : '添加板块'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {!editing && (
              <div className="space-y-2">
                <Label>板块名</Label>
                <Input
                  placeholder="例如：SaaS"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                />
              </div>
            )}
            <div className="space-y-2">
              <Label>描述</Label>
              <Textarea
                placeholder="可选"
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
              />
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
            <Button variant="outline" onClick={() => setModalOpen(false)}>取消</Button>
            <Button onClick={handleSubmit} disabled={createMutation.isPending || updateMutation.isPending}>
              {editing ? '保存' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
