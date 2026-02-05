import { useQuery } from '@tanstack/react-query'
import { Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatDateTime } from '../lib/format'
import {
  listAnalyses,
  listPosts,
  listSubreddits,
  listTags,
  type Analysis,
  type Post,
} from '../services/redditTraceApi'

export function DashboardPage() {
  const subredditsQuery = useQuery({ queryKey: ['subreddits'], queryFn: listSubreddits })
  const tagsQuery = useQuery({ queryKey: ['tags'], queryFn: listTags })
  const postsQuery = useQuery({
    queryKey: ['posts', { skip: 0, limit: 20 }],
    queryFn: () => listPosts({ skip: 0, limit: 20 }),
  })
  const valuableAnalysesQuery = useQuery({
    queryKey: ['analyses', { skip: 0, limit: 20, is_valuable: 1 }],
    queryFn: () => listAnalyses({ skip: 0, limit: 20, is_valuable: 1 }),
  })

  const kpis = [
    { title: '监控板块', value: subredditsQuery.data?.length, loading: subredditsQuery.isLoading },
    { title: '标签', value: tagsQuery.data?.length, loading: tagsQuery.isLoading },
    { title: '帖子', value: postsQuery.data?.length, loading: postsQuery.isLoading },
    { title: '有价值分析', value: valuableAnalysesQuery.data?.length, loading: valuableAnalysesQuery.isLoading },
  ]

  return (
    <div className="space-y-6">
      <Alert variant="info">
        <Info className="h-4 w-4" />
        <AlertTitle>快速开始</AlertTitle>
        <AlertDescription>
          先去 <strong>抓取</strong> 页面获取 Reddit 数据；如果你要长期监控，去"板块监控"开启定时抓取。
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <Card key={kpi.title}>
            <CardContent className="pt-4">
              <div className="text-2xl font-bold">{kpi.loading ? '-' : kpi.value ?? '-'}</div>
              <div className="text-sm text-muted-foreground">{kpi.title}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">最近帖子</CardTitle>
            <span className="text-xs text-muted-foreground">最多 20 条</span>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>标题</TableHead>
                  <TableHead className="w-20">评分</TableHead>
                  <TableHead className="w-32">时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(postsQuery.data ?? []).slice(0, 10).map((post: Post) => (
                  <TableRow key={post.id}>
                    <TableCell className="truncate max-w-[200px]">
                      <a href={post.url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                        {post.title}
                      </a>
                    </TableCell>
                    <TableCell>{post.score}</TableCell>
                    <TableCell className="text-muted-foreground text-xs">{formatDateTime(post.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">有价值分析</CardTitle>
            <span className="text-xs text-muted-foreground">最多 20 条</span>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">ID</TableHead>
                  <TableHead className="w-20">价值</TableHead>
                  <TableHead>痛点/需求/机会</TableHead>
                  <TableHead className="w-32">时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(valuableAnalysesQuery.data ?? []).slice(0, 10).map((a: Analysis) => (
                  <TableRow key={a.id}>
                    <TableCell>{a.id}</TableCell>
                    <TableCell>
                      <Badge variant="success">有价值</Badge>
                    </TableCell>
                    <TableCell>
                      {a.pain_points?.length ?? 0}/{a.user_needs?.length ?? 0}/{a.opportunities?.length ?? 0}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-xs">{formatDateTime(a.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
