import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { formatDateTime } from '../lib/format'
import { listAnalyses, type Analysis } from '../services/traceHubApi'

export function AnalysesPage() {
  const [source, setSource] = useState<string>('')
  const [isValuable, setIsValuable] = useState<string>('')
  const [pageSize, setPageSize] = useState(20)
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Analysis | null>(null)

  const analysesQuery = useQuery({
    queryKey: ['analyses', { source, isValuable, page, pageSize }],
    queryFn: () => listAnalyses({
      source: source || undefined,
      is_valuable: isValuable ? parseInt(isValuable) : undefined,
      skip: (page - 1) * pageSize,
      limit: pageSize,
    }),
  })

  const hasNextPage = (analysesQuery.data?.length ?? 0) === pageSize

  const getValueBadge = (value: number) => {
    if (value === 1) return <Badge variant="success">有价值</Badge>
    if (value === -1) return <Badge variant="destructive">无价值</Badge>
    return <Badge variant="secondary">未筛选</Badge>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>分析结果</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="space-y-1">
            <Label>来源</Label>
            <Select
              value={source || 'all'}
              onValueChange={(v) => {
                setSource(v === 'all' ? '' : v)
                setPage(1)
              }}
            >
              <SelectTrigger className="w-36">
                <SelectValue placeholder="全部" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="reddit">Reddit</SelectItem>
                <SelectItem value="hackernews">Hacker News</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <Label>价值筛选</Label>
            <Select value={isValuable || 'all'} onValueChange={(v) => { setIsValuable(v === 'all' ? '' : v); setPage(1) }}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="全部" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="1">有价值</SelectItem>
                <SelectItem value="0">未筛选</SelectItem>
                <SelectItem value="-1">无价值</SelectItem>
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
              <TableHead className="w-16">ID</TableHead>
              <TableHead className="w-24">来源</TableHead>
              <TableHead className="w-24">评论ID</TableHead>
              <TableHead className="w-20">价值</TableHead>
              <TableHead className="w-36">模型</TableHead>
              <TableHead>痛点/需求/机会</TableHead>
              <TableHead className="w-32">时间</TableHead>
              <TableHead className="w-16"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(analysesQuery.data ?? []).map((a) => (
              <TableRow key={a.id}>
                <TableCell>{a.id}</TableCell>
                <TableCell>{a.source || '-'}</TableCell>
                <TableCell>{a.comment_id}</TableCell>
                <TableCell>{getValueBadge(a.is_valuable)}</TableCell>
                <TableCell className="truncate text-xs">{a.model_used}</TableCell>
                <TableCell>
                  {a.pain_points?.length ?? 0}/{a.user_needs?.length ?? 0}/{a.opportunities?.length ?? 0}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">{formatDateTime(a.created_at)}</TableCell>
                <TableCell>
                  <Button variant="outline" size="sm" onClick={() => setSelected(a)}>
                    详情
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>

      <Sheet open={!!selected} onOpenChange={() => setSelected(null)}>
        <SheetContent className="overflow-y-auto">
          <SheetHeader>
            <SheetTitle>分析 #{selected?.id}</SheetTitle>
          </SheetHeader>
          {selected && (
            <div className="mt-4 space-y-4">
              <div className="text-sm text-muted-foreground">
                来源：{selected.source || '-'} · 评论ID：{selected.comment_id} · 模型：{selected.model_used}
              </div>
              <div className="text-sm text-muted-foreground">
                时间：{formatDateTime(selected.created_at)}
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">痛点</h4>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {(selected.pain_points ?? []).map((p, i) => <li key={i}>{p}</li>)}
                  {!(selected.pain_points?.length) && <li className="text-muted-foreground">-</li>}
                </ul>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">用户需求</h4>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {(selected.user_needs ?? []).map((n, i) => <li key={i}>{n}</li>)}
                  {!(selected.user_needs?.length) && <li className="text-muted-foreground">-</li>}
                </ul>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium">机会</h4>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {(selected.opportunities ?? []).map((o, i) => <li key={i}>{o}</li>)}
                  {!(selected.opportunities?.length) && <li className="text-muted-foreground">-</li>}
                </ul>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </Card>
  )
}
