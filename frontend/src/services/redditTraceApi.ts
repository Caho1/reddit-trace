import { http } from './http'

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
}

export type Analysis = {
  id: number
  comment_id: number
  pain_points: string[]
  user_needs: string[]
  opportunities: string[]
  model_used: string
  is_valuable: number
  created_at: string
}

export type Tag = {
  id: number
  name: string
  color: string
  description?: string | null
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
  subreddit_id?: number
  skip?: number
  limit?: number
}): Promise<Post[]> {
  const { data } = await http.get<Post[]>('/posts/', { params })
  return data
}

export async function getPost(postId: number): Promise<Post> {
  const { data } = await http.get<Post>(`/posts/${postId}`)
  return data
}

export async function listAnalyses(params: {
  is_valuable?: number
  skip?: number
  limit?: number
}): Promise<Analysis[]> {
  const { data } = await http.get<Analysis[]>('/analysis/', { params })
  return data
}

export async function listTags(): Promise<Tag[]> {
  const { data } = await http.get<Tag[]>('/tags/')
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

