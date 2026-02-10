import { http } from './http'

export type SourceName = 'reddit' | 'hackernews'

export type Subreddit = {
  id: number
  name: string
  description?: string | null
  monitor_enabled: boolean
  fetch_interval: number
  last_fetched_at?: string | null
  created_at: string
}

export type SubredditCreatePayload = {
  name: string
  description?: string | null
  monitor_enabled?: boolean
  fetch_interval?: number
}

export type SubredditUpdatePayload = {
  description?: string | null
  monitor_enabled?: boolean
  fetch_interval?: number
}

export type SourceTarget = {
  id: number
  source: SourceName | string
  target_type: string
  target_key: string
  display_name?: string | null
  description?: string | null
  monitor_enabled: boolean
  fetch_interval: number
  options: Record<string, unknown>
  last_fetched_at?: string | null
  created_at: string
  updated_at: string
}

export type SourceTargetCreatePayload = {
  source: SourceName | string
  target_type: string
  target_key: string
  display_name?: string | null
  description?: string | null
  monitor_enabled?: boolean
  fetch_interval?: number
  options?: Record<string, unknown>
}

export type SourceTargetUpdatePayload = {
  display_name?: string | null
  description?: string | null
  monitor_enabled?: boolean
  fetch_interval?: number
  options?: Record<string, unknown>
}

export type Tag = {
  id: number
  name: string
  color: string
  description?: string | null
}

export type Post = {
  id: number
  subreddit_id: number
  reddit_id: string
  title: string
  title_zh?: string | null
  content?: string | null
  content_zh?: string | null
  author: string
  url: string
  score: number
  num_comments: number
  created_at: string
  fetched_at: string
  tags?: Tag[]
  source: string
}

export type SourceComment = {
  id: number
  item_id: number
  source: string
  external_id: string
  content: string
  content_zh?: string | null
  author?: string | null
  score: number
  parent_id?: number | null
  depth: number
  created_at: string
  fetched_at: string
}

export type Analysis = {
  id: number
  comment_id: number
  source?: string | null
  item_id?: number | null
  pain_points: string[]
  user_needs: string[]
  opportunities: string[]
  model_used: string
  is_valuable: number
  created_at: string
}

export type DashboardStats = {
  now: string
  posts_total: number
  source_items_total: number
  posts_fetched_24h: number
  source_items_fetched_24h: number
  subreddits_total: number
  subreddits_monitored: number
  subreddits_fetched: number
  targets_total: number
  targets_monitored: number
  targets_fetched: number
  tags_total: number
  analyses_valuable_total: number
  source_analyses_valuable_total: number
}

export type CrawlerSubredditPost = {
  id: string
  title: string
  author: string
  selftext?: string | null
  score: number
  upvote_ratio: number
  num_comments: number
  created_utc: string
  subreddit: string
  permalink: string
  url: string
  is_self: boolean
  link_flair_text?: string | null
  thumbnail?: string | null
}

export type CrawlerComment = {
  id: string
  author: string
  body: string
  score: number
  created_utc: string
  permalink: string
  depth: number
  parent_id?: string | null
  is_submitter: boolean
}

export type CrawlerFetchPostResponse = {
  post: {
    id: string
    title: string
    author: string
    selftext?: string | null
    score: number
    upvote_ratio: number
    num_comments: number
    created_utc: string
    subreddit: string
    permalink: string
    url: string
    is_self: boolean
    link_flair_text?: string | null
  }
  comments: CrawlerComment[]
}

export type SourceCapability = {
  source: string
  display_name: string
  target_types: string[]
  [key: string]: unknown
}

export async function listSourceCapabilities(): Promise<{ sources: SourceCapability[] }> {
  const { data } = await http.get<{ sources: SourceCapability[] }>('/sources/capabilities')
  return data
}

export async function listSourceTargets(params?: {
  source?: string
  monitor_enabled?: boolean
}): Promise<SourceTarget[]> {
  const { data } = await http.get<SourceTarget[]>('/sources/targets', { params })
  return data
}

export async function createSourceTarget(payload: SourceTargetCreatePayload): Promise<SourceTarget> {
  const { data } = await http.post<SourceTarget>('/sources/targets', payload)
  return data
}

export async function updateSourceTarget(
  targetId: number,
  payload: SourceTargetUpdatePayload,
): Promise<SourceTarget> {
  const { data } = await http.patch<SourceTarget>(`/sources/targets/${targetId}`, payload)
  return data
}

export async function deleteSourceTarget(targetId: number): Promise<{ message: string }> {
  const { data } = await http.delete<{ message: string }>(`/sources/targets/${targetId}`)
  return data
}

export async function fetchSourceTarget(params: {
  target_id?: number
  source?: string
  target_type?: string
  target_key?: string
  limit?: number
  include_comments?: boolean
  comment_limit?: number
}): Promise<{
  target: SourceTarget
  items: Array<Record<string, unknown>>
  saved: {
    items_created: number
    items_updated: number
    comments_created: number
    comments_updated: number
  }
}> {
  const { data } = await http.post('/sources/fetch', params)
  return data
}

export async function listSubreddits(): Promise<Subreddit[]> {
  const { data } = await http.get<Subreddit[]>('/subreddits/')
  return data
}

export async function createSubreddit(payload: SubredditCreatePayload): Promise<Subreddit> {
  const { data } = await http.post<Subreddit>('/subreddits/', payload)
  return data
}

export async function updateSubreddit(
  subredditId: number,
  payload: SubredditUpdatePayload,
): Promise<Subreddit> {
  const { data } = await http.patch<Subreddit>(`/subreddits/${subredditId}`, payload)
  return data
}

export async function deleteSubreddit(subredditId: number): Promise<{ message: string }> {
  const { data } = await http.delete<{ message: string }>(`/subreddits/${subredditId}`)
  return data
}

export async function listPosts(params: {
  source?: string
  target_id?: number
  subreddit_id?: number
  tag_id?: number
  skip?: number
  limit?: number
}): Promise<Post[]> {
  const { data } = await http.get<Post[]>('/posts', { params })
  return data
}

export async function getPost(postId: number): Promise<Post> {
  const { data } = await http.get<Post>(`/posts/${postId}`)
  return data
}

export async function listPostTags(postId: number): Promise<Tag[]> {
  const { data } = await http.get<Tag[]>(`/posts/${postId}/tags`)
  return data
}

export async function setPostTags(postId: number, tagIds: number[]): Promise<Tag[]> {
  const { data } = await http.put<Tag[]>(`/posts/${postId}/tags`, { tag_ids: tagIds })
  return data
}

export async function listSourceItemTags(itemId: number): Promise<Tag[]> {
  const { data } = await http.get<Tag[]>(`/sources/items/${itemId}/tags`)
  return data
}

export async function setSourceItemTags(itemId: number, tagIds: number[]): Promise<Tag[]> {
  const { data } = await http.put<Tag[]>(`/sources/items/${itemId}/tags`, { tag_ids: tagIds })
  return data
}

export async function listSourceItemComments(params: {
  item_id: number
  skip?: number
  limit?: number
}): Promise<SourceComment[]> {
  const { data } = await http.get<SourceComment[]>(`/sources/items/${params.item_id}/comments`, {
    params: {
      skip: params.skip,
      limit: params.limit,
    },
  })
  return data
}

export async function listAnalyses(params: {
  source?: string
  is_valuable?: number
  skip?: number
  limit?: number
}): Promise<Analysis[]> {
  const { data } = await http.get<Analysis[]>('/analysis/sources', { params })
  return data
}

export async function listTags(): Promise<Tag[]> {
  const { data } = await http.get<Tag[]>('/tags/')
  return data
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await http.get<DashboardStats>('/dashboard/stats')
  return data
}

export async function createTag(payload: {
  name: string
  color?: string
  description?: string | null
}): Promise<Tag> {
  const { data } = await http.post<Tag>('/tags/', payload)
  return data
}

export async function deleteTag(tagId: number): Promise<{ message: string }> {
  const { data } = await http.delete<{ message: string }>(`/tags/${tagId}`)
  return data
}

export async function crawlerFetchPost(url: string): Promise<CrawlerFetchPostResponse> {
  const { data } = await http.post<CrawlerFetchPostResponse>('/crawler/fetch-post', { url })
  return data
}

export async function crawlerFetchSubreddit(params: {
  name: string
  sort?: string
  limit?: number
}): Promise<{ posts: CrawlerSubredditPost[] }> {
  const { data } = await http.post<{ posts: CrawlerSubredditPost[] }>(
    '/crawler/fetch-subreddit',
    params,
  )
  return data
}
