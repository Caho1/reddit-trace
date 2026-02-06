import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ExternalLink } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { formatDateTime } from '../lib/format'
import {
  listPosts,
  listSubreddits,
  listTags,
  setPostTags,
  type Post,
  type Subreddit,
  type Tag,
} from '../services/redditTraceApi'

export function PostsPage() {
  const queryClient = useQueryClient()
  const [subredditId, setSubredditId] = useState<string>('')
  const [tagId, setTagId] = useState<string>('')
  const [pageSize, setPageSize] = useState(20)
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Post | null>(null)
  const [addTagId, setAddTagId] = useState<string>('')

  const subredditsQuery = useQuery({ queryKey: ['subreddits'], queryFn: listSubreddits })
  const tagsQuery = useQuery({ queryKey: ['tags'], queryFn: listTags })

  const setTagsMutation = useMutation({
    mutationFn: (args: { postId: number; tagIds: number[] }) => setPostTags(args.postId, args.tagIds),
    onSuccess: async (tags, vars) => {
      await queryClient.invalidateQueries({ queryKey: ['posts'] })
      if (selected?.id === vars.postId) {
        setSelected({ ...selected, tags })
      }
    },
  })

  const postsQuery = useQuery({
    queryKey: ['posts', { subredditId, tagId, page, pageSize }],
    queryFn: () => listPosts({
      subreddit_id: subredditId ? parseInt(subredditId) : undefined,
      tag_id: tagId ? parseInt(tagId) : undefined,
      skip: (page - 1) * pageSize,
      limit: pageSize,
    }),
  })

  const subredditMap = new Map<number, string>()
  for (const s of subredditsQuery.data ?? []) {
    subredditMap.set(s.id, s.name)
  }

  const hasNextPage = (postsQuery.data?.length ?? 0) === pageSize

  return (
    <Card>
      <CardHeader>
        <CardTitle>帖子</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="space-y-1">
            <Label>板块</Label>
            <Select value={subredditId || 'all'} onValueChange={(v) => { setSubredditId(v === 'all' ? '' : v); setPage(1) }}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="全部" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                {(subredditsQuery.data ?? []).map((s: Subreddit) => (
                  <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>标签</Label>
            <Select value={tagId || 'all'} onValueChange={(v) => { setTagId(v === 'all' ? '' : v); setPage(1) }}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="全部" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                {(tagsQuery.data ?? []).map((t: Tag) => (
                  <SelectItem key={t.id} value={String(t.id)}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>每页</Label>
            <Select value={String(pageSize)} onValueChange={(v) => { setPageSize(parseInt(v)); setPage(1) }}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[10, 20, 50, 100].map((n) => (
                  <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              上一页
            </Button>
            <span className="text-sm text-muted-foreground">第 {page} 页</span>
            <Button variant="outline" size="sm" disabled={!hasNextPage} onClick={() => setPage(p => p + 1)}>
              下一页
            </Button>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>标题</TableHead>
              <TableHead className="w-28">板块</TableHead>
              <TableHead className="w-28">作者</TableHead>
              <TableHead className="w-16">评分</TableHead>
              <TableHead className="w-16">评论</TableHead>
              <TableHead className="w-32">时间</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(postsQuery.data ?? []).map((post) => (
              <TableRow key={post.id}>
                <TableCell>
                  <div className="space-y-1">
                    <Button
                      type="button"
                      variant="link"
                      className="h-auto max-w-[300px] truncate p-0 text-left"
                      onClick={() => setSelected(post)}
                    >
                      {post.title}
                    </Button>
                    {(post.tags?.length ?? 0) > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {(post.tags ?? []).slice(0, 6).map((t) => (
                          <Badge
                            key={t.id}
                            variant="secondary"
                            className="text-white"
                            style={{ backgroundColor: t.color }}
                          >
                            {t.name}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>{subredditMap.get(post.subreddit_id) || `#${post.subreddit_id}`}</TableCell>
                <TableCell className="truncate">{post.author}</TableCell>
                <TableCell>{post.score}</TableCell>
                <TableCell>{post.num_comments}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{formatDateTime(post.created_at)}</TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground"
                    asChild
                  >
                    <a href={post.url} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-4 w-4" />
                      <span className="sr-only">打开原帖</span>
                    </a>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>

      <Sheet open={!!selected} onOpenChange={() => { setSelected(null); setAddTagId('') }}>
        <SheetContent className="overflow-y-auto">
          <SheetHeader>
            <SheetTitle>{selected?.title}</SheetTitle>
          </SheetHeader>
          {selected && (
            <div className="mt-4 space-y-4">
              <div className="text-sm text-muted-foreground">
                作者：{selected.author} · 评分：{selected.score} · 评论：{selected.num_comments}
              </div>
              <div className="text-sm text-muted-foreground">
                创建：{formatDateTime(selected.created_at)} · 抓取：{formatDateTime(selected.fetched_at)}
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">标签</h4>
                <div className="flex flex-wrap gap-2">
                  {(selected.tags ?? []).map((t) => (
                    <Badge
                      key={t.id}
                      variant="secondary"
                      className="text-white"
                      style={{ backgroundColor: t.color }}
                    >
                      <span className="mr-1">{t.name}</span>
                      <button
                        type="button"
                        className="rounded px-1 hover:bg-white/20"
                        onClick={() => {
                          const next = (selected.tags ?? []).filter(x => x.id !== t.id).map(x => x.id)
                          setTagsMutation.mutate({ postId: selected.id, tagIds: next })
                        }}
                        disabled={setTagsMutation.isPending}
                        aria-label={`移除标签 ${t.name}`}
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                  {!(selected.tags?.length) && <span className="text-sm text-muted-foreground">-</span>}
                </div>

                <div className="flex gap-2 items-end">
                  <div className="space-y-1 flex-1">
                    <Label>添加标签</Label>
                    <Select
                      value={addTagId || 'none'}
                      onValueChange={(v) => setAddTagId(v === 'none' ? '' : v)}
                      disabled={setTagsMutation.isPending}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择一个标签" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-</SelectItem>
                        {(tagsQuery.data ?? []).map((t: Tag) => (
                          <SelectItem key={t.id} value={String(t.id)}>{t.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={!addTagId || setTagsMutation.isPending}
                    onClick={() => {
                      const current = new Set((selected.tags ?? []).map(t => t.id))
                      current.add(parseInt(addTagId))
                      setTagsMutation.mutate({ postId: selected.id, tagIds: Array.from(current) })
                      setAddTagId('')
                    }}
                  >
                    添加
                  </Button>
                </div>
              </div>
              <Button variant="link" className="h-auto p-0 text-sm" asChild>
                <a href={selected.url} target="_blank" rel="noreferrer">
                  打开原帖
                </a>
              </Button>

              <div className="space-y-2">
                <h4 className="font-medium">内容（原文）</h4>
                <div className="p-3 bg-muted text-sm whitespace-pre-wrap">
                  {selected.content || <span className="text-muted-foreground">-</span>}
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">内容（中文）</h4>
                <div className="p-3 bg-muted text-sm whitespace-pre-wrap">
                  {selected.content_zh || <span className="text-muted-foreground">-</span>}
                </div>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </Card>
  )
}
