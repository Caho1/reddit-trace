import { useMemo, useState } from 'react'
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
  listSourceTargets,
  listTags,
  setPostTags,
  setSourceItemTags,
  type Post,
  type Subreddit,
  type SourceTarget,
  type Tag,
} from '../services/traceHubApi'

type SourceFilter = 'all' | 'reddit' | 'hackernews'

const SOURCE_LABEL: Record<string, string> = {
  reddit: 'Reddit',
  hackernews: 'Hacker News',
}

function getSourceLabel(source: string): string {
  return SOURCE_LABEL[source] ?? source
}

export function PostsPage() {
  const queryClient = useQueryClient()
  const [source, setSource] = useState<SourceFilter>('all')
  const [subredditId, setSubredditId] = useState<string>('')
  const [targetId, setTargetId] = useState<string>('')
  const [tagId, setTagId] = useState<string>('')
  const [pageSize, setPageSize] = useState(20)
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Post | null>(null)
  const [addTagId, setAddTagId] = useState<string>('')

  const targetLabel =
    source === 'reddit'
      ? '监控目标（可选）'
      : source === 'hackernews'
        ? 'HN 目标'
        : '监控目标'

  const subredditsQuery = useQuery({ queryKey: ['subreddits'], queryFn: listSubreddits })
  const targetsQuery = useQuery({
    queryKey: ['source-targets', { source }],
    queryFn: () => listSourceTargets(source === 'all' ? undefined : { source }),
  })
  const tagsQuery = useQuery({ queryKey: ['tags'], queryFn: listTags })

  const setTagsMutation = useMutation({
    mutationFn: async (args: { post: Post; tagIds: number[] }) => {
      try {
        return await setSourceItemTags(args.post.id, args.tagIds)
      } catch (error) {
        // 兼容旧帖子 ID（legacy posts 表）
        if (args.post.source === 'reddit') {
          return setPostTags(args.post.id, args.tagIds)
        }
        throw error
      }
    },
    onSuccess: async (tags, vars) => {
      await queryClient.invalidateQueries({ queryKey: ['posts'] })
      if (selected?.id === vars.post.id) {
        setSelected({ ...selected, tags })
      }
    },
  })

  const postsQuery = useQuery({
    queryKey: ['posts', { source, subredditId, targetId, tagId, page, pageSize }],
    queryFn: () => {
      return listPosts({
        source: source === 'all' ? undefined : source,
        target_id: targetId ? parseInt(targetId) : undefined,
        subreddit_id: source === 'reddit' && subredditId ? parseInt(subredditId) : undefined,
        tag_id: tagId ? parseInt(tagId) : undefined,
        skip: (page - 1) * pageSize,
        limit: pageSize,
      })
    },
  })

  const subredditMap = new Map<number, string>()
  for (const subreddit of subredditsQuery.data ?? []) {
    subredditMap.set(subreddit.id, subreddit.name)
  }

  const targetMap = new Map<number, SourceTarget>()
  for (const target of targetsQuery.data ?? []) {
    targetMap.set(target.id, target)
  }

  const targetOptions = useMemo(() => {
    const allTargets = targetsQuery.data ?? []
    if (source === 'all') {
      return allTargets
    }
    return allTargets.filter((target) => target.source === source)
  }, [targetsQuery.data, source])

  const resolveTargetText = (post: Post): string => {
    if (post.subreddit_id) {
      const matchedTarget = targetMap.get(post.subreddit_id)
      if (matchedTarget) {
        return matchedTarget.display_name || matchedTarget.target_key
      }
    }

    if (post.source === 'reddit') {
      return subredditMap.get(post.subreddit_id) || '-'
    }
    return '-'
  }

  const hasNextPage = (postsQuery.data?.length ?? 0) === pageSize

  return (
    <Card>
      <CardHeader>
        <CardTitle>内容</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="space-y-1">
            <Label>来源</Label>
            <Select
              value={source}
              onValueChange={(value) => {
                setSource(value as SourceFilter)
                setSubredditId('')
                setTargetId('')
                setPage(1)
              }}
            >
              <SelectTrigger className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="reddit">Reddit</SelectItem>
                <SelectItem value="hackernews">Hacker News</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {source === 'reddit' && (
            <div className="space-y-1">
              <Label>板块</Label>
              <Select
                value={subredditId || 'all'}
                onValueChange={(value) => {
                  setSubredditId(value === 'all' ? '' : value)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="全部" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  {(subredditsQuery.data ?? []).map((subreddit: Subreddit) => (
                    <SelectItem key={subreddit.id} value={String(subreddit.id)}>
                      {subreddit.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-1">
            <Label>{targetLabel}</Label>
            <Select
              value={targetId || 'all'}
              onValueChange={(value) => {
                setTargetId(value === 'all' ? '' : value)
                setPage(1)
              }}
            >
              <SelectTrigger className="w-52">
                <SelectValue placeholder="全部" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                {targetOptions.map((target) => (
                  <SelectItem key={target.id} value={String(target.id)}>
                    {`${getSourceLabel(target.source)} · ${target.display_name || target.target_key}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label>标签</Label>
            <Select
              value={tagId || 'all'}
              onValueChange={(value) => {
                setTagId(value === 'all' ? '' : value)
                setPage(1)
              }}
            >
              <SelectTrigger className="w-44">
                <SelectValue placeholder="全部" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                {(tagsQuery.data ?? []).map((tag: Tag) => (
                  <SelectItem key={tag.id} value={String(tag.id)}>
                    {tag.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label>每页</Label>
            <Select
              value={String(pageSize)}
              onValueChange={(value) => {
                setPageSize(parseInt(value))
                setPage(1)
              }}
            >
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[10, 20, 50, 100].map((n) => (
                  <SelectItem key={n} value={String(n)}>
                    {n}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </Button>
            <span className="text-sm text-muted-foreground">第 {page} 页</span>
            <Button variant="outline" size="sm" disabled={!hasNextPage} onClick={() => setPage((p) => p + 1)}>
              下一页
            </Button>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-24">来源</TableHead>
              <TableHead className="w-40">目标</TableHead>
              <TableHead>标题</TableHead>
              <TableHead className="w-24">作者</TableHead>
              <TableHead className="w-16">评分</TableHead>
              <TableHead className="w-16">评论</TableHead>
              <TableHead className="w-32">时间</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {(postsQuery.data ?? []).map((post) => (
              <TableRow key={`${post.source}-${post.id}`}>
                <TableCell>
                  <Badge variant="outline">{getSourceLabel(post.source)}</Badge>
                </TableCell>
                <TableCell className="truncate max-w-[180px] text-muted-foreground text-xs">
                  {resolveTargetText(post)}
                </TableCell>
                <TableCell className="truncate max-w-[360px]">
                  <button
                    type="button"
                    className="text-left text-primary hover:underline"
                    onClick={() => setSelected(post)}
                  >
                    {post.title}
                  </button>
                </TableCell>
                <TableCell className="truncate">{post.author}</TableCell>
                <TableCell>{post.score}</TableCell>
                <TableCell>{post.num_comments}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{formatDateTime(post.created_at)}</TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" asChild>
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

      <Sheet
        open={!!selected}
        onOpenChange={() => {
          setSelected(null)
          setAddTagId('')
        }}
      >
        <SheetContent className="overflow-y-auto">
          <SheetHeader>
            <SheetTitle>{selected?.title}</SheetTitle>
          </SheetHeader>
          {selected && (
            <div className="mt-4 space-y-4">
              <div className="text-sm text-muted-foreground">
                来源：{getSourceLabel(selected.source)} · 作者：{selected.author} · 评分：{selected.score} · 评论：
                {selected.num_comments}
              </div>
              <div className="text-sm text-muted-foreground">
                创建：{formatDateTime(selected.created_at)} · 抓取：{formatDateTime(selected.fetched_at)}
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">标签</h4>
                <div className="flex flex-wrap gap-2">
                  {(selected.tags ?? []).map((tag) => (
                    <Badge
                      key={tag.id}
                      variant="secondary"
                      className="text-white"
                      style={{ backgroundColor: tag.color }}
                    >
                      <span className="mr-1">{tag.name}</span>
                      <button
                        type="button"
                        className="rounded px-1 hover:bg-white/20"
                        onClick={() => {
                          const next = (selected.tags ?? []).filter((x) => x.id !== tag.id).map((x) => x.id)
                          setTagsMutation.mutate({ post: selected, tagIds: next })
                        }}
                        disabled={setTagsMutation.isPending}
                        aria-label={`移除标签 ${tag.name}`}
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
                      onValueChange={(value) => setAddTagId(value === 'none' ? '' : value)}
                      disabled={setTagsMutation.isPending}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择一个标签" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">-</SelectItem>
                        {(tagsQuery.data ?? []).map((tag: Tag) => (
                          <SelectItem key={tag.id} value={String(tag.id)}>
                            {tag.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={!addTagId || setTagsMutation.isPending}
                    onClick={() => {
                      const current = new Set((selected.tags ?? []).map((t) => t.id))
                      current.add(parseInt(addTagId))
                      setTagsMutation.mutate({ post: selected, tagIds: Array.from(current) })
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
