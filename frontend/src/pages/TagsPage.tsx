import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
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
import { getErrorMessage } from '../lib/errors'
import { createTag, deleteTag, listTags, type Tag } from '../services/redditTraceApi'

export function TagsPage() {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [formName, setFormName] = useState('')
  const [formColor, setFormColor] = useState('#dc2626')
  const [formDesc, setFormDesc] = useState('')

  const tagsQuery = useQuery({ queryKey: ['tags'], queryFn: listTags })

  const createMutation = useMutation({
    mutationFn: createTag,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['tags'] })
      setModalOpen(false)
      setError(null)
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTag,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['tags'] })
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const openCreate = () => {
    setFormName('')
    setFormColor('#dc2626')
    setFormDesc('')
    setModalOpen(true)
  }

  const handleSubmit = () => {
    if (!formName.trim()) return
    createMutation.mutate({
      name: formName.trim(),
      color: formColor,
      description: formDesc,
    })
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>标签</CardTitle>
        <Button onClick={openCreate}>
          <Plus className="w-4 h-4 mr-1" />
          新建
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
              <TableHead>名称</TableHead>
              <TableHead>描述</TableHead>
              <TableHead className="w-28">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(tagsQuery.data ?? []).map((tag: Tag) => (
              <TableRow key={tag.id}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="secondary"
                      className="text-white"
                      style={{ backgroundColor: tag.color }}
                    >
                      {tag.name}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{tag.color}</span>
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">{tag.description || '-'}</TableCell>
                <TableCell>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="destructive" size="sm">删除</Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>确定删除？</AlertDialogTitle>
                        <AlertDialogDescription>
                          删除标签 "{tag.name}" 后无法恢复。
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>取消</AlertDialogCancel>
                        <AlertDialogAction onClick={() => deleteMutation.mutate(tag.id)}>
                          删除
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建标签</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>名称</Label>
              <Input
                placeholder="例如：支付"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>颜色</Label>
              <Input
                type="color"
                value={formColor}
                onChange={(e) => setFormColor(e.target.value)}
                className="h-10 w-20 p-1"
              />
            </div>
            <div className="space-y-2">
              <Label>描述</Label>
              <Textarea
                placeholder="可选"
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalOpen(false)}>取消</Button>
            <Button onClick={handleSubmit} disabled={createMutation.isPending}>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
