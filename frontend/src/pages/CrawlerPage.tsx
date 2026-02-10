import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ExternalLink, Plus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { formatDateTime } from '../lib/format'
import { getErrorMessage } from '../lib/errors'
import {
  createSourceTarget,
  fetchSourceTarget,
  listSourceTargets,
  type SourceName,
  type SourceTarget,
} from '../services/traceHubApi'

const SOURCE_LABEL: Record<SourceName, string> = {
  reddit: 'Reddit',
  hackernews: 'Hacker News',
}

function formatTargetDisplay(target: SourceTarget): string {
  return `${SOURCE_LABEL[target.source as SourceName] ?? target.source} · ${target.display_name || target.target_key}`
}

export function CrawlerPage() {
  const queryClient = useQueryClient()

  const [error, setError] = useState<string | null>(null)
  const [source, setSource] = useState<SourceName>('reddit')

  const [redditSubName, setRedditSubName] = useState('')
  const [redditSort, setRedditSort] = useState('hot')
  const [redditLimit, setRedditLimit] = useState('25')
  const [redditPostUrl, setRedditPostUrl] = useState('')

  const [hnFeed, setHnFeed] = useState('topstories')
  const [hnLimit, setHnLimit] = useState('30')
  const [hnStoryId, setHnStoryId] = useState('')

  const [selectedTargetId, setSelectedTargetId] = useState<string>('')

  const targetsQuery = useQuery({ queryKey: ['source-targets'], queryFn: () => listSourceTargets() })

  const currentTargets = useMemo(() => {
    return (targetsQuery.data ?? []).filter((target) => target.source === source)
  }, [targetsQuery.data, source])

  const fetchMutation = useMutation({
    mutationFn: fetchSourceTarget,
    onSuccess: async () => {
      setError(null)
      await queryClient.invalidateQueries({ queryKey: ['posts'] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      await queryClient.invalidateQueries({ queryKey: ['source-targets'] })
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const fetchSummary = fetchMutation.data?.saved

  const addTargetMutation = useMutation({
    mutationFn: createSourceTarget,
    onSuccess: async (target) => {
      setError(null)
      setSelectedTargetId(String(target.id))
      await queryClient.invalidateQueries({ queryKey: ['source-targets'] })
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const renderTargetRows = (targets: SourceTarget[]) => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-20">来源</TableHead>
          <TableHead className="w-24">类型</TableHead>
          <TableHead>目标</TableHead>
          <TableHead className="w-20">监控</TableHead>
          <TableHead className="w-28">间隔(分钟)</TableHead>
          <TableHead className="w-36">上次抓取</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {targets.map((target) => (
          <TableRow key={target.id}>
            <TableCell>
              <Badge variant="outline">{SOURCE_LABEL[target.source as SourceName] ?? target.source}</Badge>
            </TableCell>
            <TableCell>{target.target_type}</TableCell>
            <TableCell className="truncate max-w-[300px]">
              {target.display_name || target.target_key}
            </TableCell>
            <TableCell>{target.monitor_enabled ? '开' : '关'}</TableCell>
            <TableCell>{target.fetch_interval}</TableCell>
            <TableCell className="text-xs text-muted-foreground">
              {formatDateTime(target.last_fetched_at)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>抓取</CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="manual">
          <TabsList>
            <TabsTrigger value="manual">手动抓取</TabsTrigger>
            <TabsTrigger value="targets">目标管理</TabsTrigger>
          </TabsList>

          <TabsContent value="manual" className="space-y-6">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="space-y-1">
                <Label>来源</Label>
                <Select
                  value={source}
                  onValueChange={(value) => {
                    setSource(value as SourceName)
                    setSelectedTargetId('')
                  }}
                >
                  <SelectTrigger className="w-44">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="reddit">Reddit</SelectItem>
                    <SelectItem value="hackernews">Hacker News</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <Label>使用已有目标</Label>
                <Select
                  value={selectedTargetId || 'none'}
                  onValueChange={(value) => setSelectedTargetId(value === 'none' ? '' : value)}
                >
                  <SelectTrigger className="w-72">
                    <SelectValue placeholder="可选：选择已有目标快速抓取" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">不使用</SelectItem>
                    {currentTargets.map((target) => (
                      <SelectItem key={target.id} value={String(target.id)}>
                        {formatTargetDisplay(target)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button
                disabled={!selectedTargetId || fetchMutation.isPending}
                onClick={() =>
                  selectedTargetId &&
                  fetchMutation.mutate({
                    target_id: parseInt(selectedTargetId),
                    limit: 50,
                  })
                }
              >
                {fetchMutation.isPending ? '抓取中...' : '抓取所选目标'}
              </Button>
            </div>

            {fetchSummary && (
              <Alert>
                <AlertDescription>
                  抓取完成：新增内容 {fetchSummary.items_created} 条，更新内容 {fetchSummary.items_updated} 条，新增评论{' '}
                  {fetchSummary.comments_created} 条，更新评论 {fetchSummary.comments_updated} 条。
                </AlertDescription>
              </Alert>
            )}

            {source === 'reddit' && (
              <div className="space-y-6">
                <div className="space-y-3">
                  <h4 className="font-medium">抓取 Reddit 板块</h4>
                  <div className="flex flex-wrap gap-4 items-end">
                    <div className="space-y-1">
                      <Label>板块名</Label>
                      <Input
                        placeholder="例如：SaaS"
                        value={redditSubName}
                        onChange={(e) => setRedditSubName(e.target.value)}
                        className="w-48"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>排序</Label>
                      <Select value={redditSort} onValueChange={setRedditSort}>
                        <SelectTrigger className="w-28">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="hot">hot</SelectItem>
                          <SelectItem value="new">new</SelectItem>
                          <SelectItem value="top">top</SelectItem>
                          <SelectItem value="rising">rising</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1">
                      <Label>数量</Label>
                      <Input
                        type="number"
                        value={redditLimit}
                        onChange={(e) => setRedditLimit(e.target.value)}
                        className="w-24"
                      />
                    </div>
                    <Button
                      disabled={!redditSubName || fetchMutation.isPending}
                      onClick={() =>
                        fetchMutation.mutate({
                          source: 'reddit',
                          target_type: 'subreddit',
                          target_key: redditSubName,
                          limit: parseInt(redditLimit) || 25,
                          include_comments: false,
                          comment_limit: 20,
                        })
                      }
                    >
                      {fetchMutation.isPending ? '抓取中...' : '开始抓取'}
                    </Button>
                    <Button
                      variant="outline"
                      disabled={!redditSubName || addTargetMutation.isPending}
                      onClick={() =>
                        addTargetMutation.mutate({
                          source: 'reddit',
                          target_type: 'subreddit',
                          target_key: redditSubName,
                          display_name: `r/${redditSubName}`,
                          monitor_enabled: true,
                          fetch_interval: 60,
                          options: {
                            sort: redditSort,
                            limit: parseInt(redditLimit) || 25,
                            include_comments: false,
                            comment_limit: 20,
                          },
                        })
                      }
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      添加到监控
                    </Button>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="font-medium">抓取 Reddit 帖子</h4>
                  <div className="flex gap-4 items-end">
                    <div className="flex-1 space-y-1">
                      <Label>帖子 URL</Label>
                      <Input
                        placeholder="https://www.reddit.com/r/.../comments/.../..."
                        value={redditPostUrl}
                        onChange={(e) => setRedditPostUrl(e.target.value)}
                      />
                    </div>
                    <Button
                      disabled={!redditPostUrl || fetchMutation.isPending}
                      onClick={() =>
                        fetchMutation.mutate({
                          source: 'reddit',
                          target_type: 'post_url',
                          target_key: redditPostUrl,
                          limit: 1,
                          include_comments: true,
                          comment_limit: 100,
                        })
                      }
                    >
                      {fetchMutation.isPending ? '抓取中...' : '开始抓取'}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {source === 'hackernews' && (
              <div className="space-y-6">
                <div className="space-y-3">
                  <h4 className="font-medium">抓取 HN Feed</h4>
                  <div className="flex flex-wrap gap-4 items-end">
                    <div className="space-y-1">
                      <Label>Feed</Label>
                      <Select value={hnFeed} onValueChange={setHnFeed}>
                        <SelectTrigger className="w-44">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="topstories">topstories</SelectItem>
                          <SelectItem value="newstories">newstories</SelectItem>
                          <SelectItem value="askstories">askstories</SelectItem>
                          <SelectItem value="showstories">showstories</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1">
                      <Label>数量</Label>
                      <Input
                        type="number"
                        value={hnLimit}
                        onChange={(e) => setHnLimit(e.target.value)}
                        className="w-24"
                      />
                    </div>
                    <Button
                      disabled={fetchMutation.isPending}
                      onClick={() =>
                        fetchMutation.mutate({
                          source: 'hackernews',
                          target_type: 'feed',
                          target_key: hnFeed,
                          limit: parseInt(hnLimit) || 30,
                          include_comments: false,
                          comment_limit: 20,
                        })
                      }
                    >
                      {fetchMutation.isPending ? '抓取中...' : '开始抓取'}
                    </Button>
                    <Button
                      variant="outline"
                      disabled={addTargetMutation.isPending}
                      onClick={() =>
                        addTargetMutation.mutate({
                          source: 'hackernews',
                          target_type: 'feed',
                          target_key: hnFeed,
                          display_name: `HN ${hnFeed}`,
                          monitor_enabled: true,
                          fetch_interval: 60,
                          options: {
                            limit: parseInt(hnLimit) || 30,
                            include_comments: false,
                            comment_limit: 20,
                          },
                        })
                      }
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      添加到监控
                    </Button>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="font-medium">抓取 HN Story</h4>
                  <div className="flex gap-4 items-end">
                    <div className="flex-1 space-y-1">
                      <Label>Story ID</Label>
                      <Input
                        placeholder="例如：8863"
                        value={hnStoryId}
                        onChange={(e) => setHnStoryId(e.target.value)}
                      />
                    </div>
                    <Button
                      disabled={!hnStoryId || fetchMutation.isPending}
                      onClick={() =>
                        fetchMutation.mutate({
                          source: 'hackernews',
                          target_type: 'story',
                          target_key: hnStoryId,
                          limit: 1,
                          include_comments: true,
                          comment_limit: 100,
                        })
                      }
                    >
                      {fetchMutation.isPending ? '抓取中...' : '开始抓取'}
                    </Button>
                    {hnStoryId && (
                      <Button variant="ghost" size="icon" className="h-9 w-9 text-muted-foreground" asChild>
                        <a
                          href={`https://news.ycombinator.com/item?id=${hnStoryId}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <ExternalLink className="h-4 w-4" />
                          <span className="sr-only">打开 HN 页面</span>
                        </a>
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="targets" className="space-y-4">
            <div className="text-sm text-muted-foreground">已注册抓取目标（统一调度与扩展入口）</div>
            {renderTargetRows(targetsQuery.data ?? [])}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
