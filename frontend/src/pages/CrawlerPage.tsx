import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ExternalLink, Plus } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
  createSubreddit,
  crawlerFetchPost,
  crawlerFetchSubreddit,
  type CrawlerComment,
  type CrawlerFetchPostResponse,
  type CrawlerSubredditPost,
} from '../services/redditTraceApi'

export function CrawlerPage() {
  const [subredditPosts, setSubredditPosts] = useState<CrawlerSubredditPost[]>([])
  const [postResult, setPostResult] = useState<CrawlerFetchPostResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Form states
  const [subName, setSubName] = useState('')
  const [subSort, setSubSort] = useState('hot')
  const [subLimit, setSubLimit] = useState('25')
  const [postUrl, setPostUrl] = useState('')

  const fetchSubredditMutation = useMutation({
    mutationFn: crawlerFetchSubreddit,
    onSuccess: (res) => {
      setSubredditPosts(res.posts ?? [])
      setError(null)
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const fetchPostMutation = useMutation({
    mutationFn: crawlerFetchPost,
    onSuccess: (res) => {
      setPostResult(res)
      setError(null)
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const addMonitorMutation = useMutation({
    mutationFn: createSubreddit,
    onSuccess: () => setError(null),
    onError: (err) => setError(getErrorMessage(err)),
  })

  const subredditName = subredditPosts[0]?.subreddit
  const comments = (postResult?.comments ?? []).slice(0, 200)

  return (
    <Card>
      <CardHeader>
        <CardTitle>抓取</CardTitle>
      </CardHeader>
      <CardContent>
        {error && <div className="mb-4 p-3 bg-destructive/10 text-destructive text-sm">{error}</div>}

        <Tabs defaultValue="subreddit">
          <TabsList>
            <TabsTrigger value="subreddit">抓取板块</TabsTrigger>
            <TabsTrigger value="post">抓取帖子</TabsTrigger>
          </TabsList>

          <TabsContent value="subreddit" className="space-y-4">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="space-y-1">
                <Label>板块名</Label>
                <Input
                  placeholder="例如：SaaS"
                  value={subName}
                  onChange={(e) => setSubName(e.target.value)}
                  className="w-48"
                />
              </div>
              <div className="space-y-1">
                <Label>排序</Label>
                <Select value={subSort} onValueChange={setSubSort}>
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
                  value={subLimit}
                  onChange={(e) => setSubLimit(e.target.value)}
                  className="w-20"
                />
              </div>
              <Button
                onClick={() => fetchSubredditMutation.mutate({
                  name: subName,
                  sort: subSort as 'hot' | 'new' | 'top' | 'rising',
                  limit: parseInt(subLimit) || 25,
                })}
                disabled={!subName || fetchSubredditMutation.isPending}
              >
                {fetchSubredditMutation.isPending ? '抓取中...' : '开始抓取'}
              </Button>
              <Button
                variant="outline"
                disabled={!subredditName || addMonitorMutation.isPending}
                onClick={() => subredditName && addMonitorMutation.mutate({
                  name: subredditName,
                  monitor_enabled: true,
                  fetch_interval: 60,
                })}
              >
                <Plus className="w-4 h-4 mr-1" />
                添加到监控
              </Button>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>标题</TableHead>
                  <TableHead className="w-28">作者</TableHead>
                  <TableHead className="w-16">评分</TableHead>
                  <TableHead className="w-16">评论</TableHead>
                  <TableHead className="w-32">时间</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {subredditPosts.map((post) => (
                  <TableRow key={post.id}>
                    <TableCell className="truncate max-w-[300px]">
                      <a href={post.url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                        {post.title}
                      </a>
                    </TableCell>
                    <TableCell className="truncate">{post.author}</TableCell>
                    <TableCell>{post.score}</TableCell>
                    <TableCell>{post.num_comments}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDateTime(post.created_utc)}</TableCell>
                    <TableCell>
                      <a href={post.url} target="_blank" rel="noreferrer">
                        <ExternalLink className="w-4 h-4 text-muted-foreground" />
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>

          <TabsContent value="post" className="space-y-4">
            <div className="flex gap-4 items-end">
              <div className="flex-1 space-y-1">
                <Label>帖子 URL</Label>
                <Input
                  placeholder="https://www.reddit.com/r/.../comments/.../..."
                  value={postUrl}
                  onChange={(e) => setPostUrl(e.target.value)}
                />
              </div>
              <Button
                onClick={() => fetchPostMutation.mutate(postUrl)}
                disabled={!postUrl || fetchPostMutation.isPending}
              >
                {fetchPostMutation.isPending ? '抓取中...' : '开始抓取'}
              </Button>
            </div>

            {postResult && (
              <div className="space-y-4">
                <Card>
                  <CardHeader className="py-3">
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-base">{postResult.post.title}</CardTitle>
                      <Badge variant="secondary">r/{postResult.post.subreddit}</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      作者：{postResult.post.author} · 评分：{postResult.post.score} · 评论：{postResult.post.num_comments}
                    </div>
                  </CardHeader>
                </Card>

                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-32">作者</TableHead>
                      <TableHead>内容</TableHead>
                      <TableHead className="w-16">评分</TableHead>
                      <TableHead className="w-32">时间</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {comments.map((c: CrawlerComment) => (
                      <TableRow key={c.id}>
                        <TableCell className="truncate">{c.author}</TableCell>
                        <TableCell>
                          <div style={{ paddingLeft: Math.min(100, c.depth * 12) }} className="whitespace-pre-wrap text-sm">
                            {c.body}
                          </div>
                        </TableCell>
                        <TableCell>{c.score}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{formatDateTime(c.created_utc)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {!postResult && (
              <p className="text-muted-foreground text-sm">输入 URL 后开始抓取，结果会显示在这里。</p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
