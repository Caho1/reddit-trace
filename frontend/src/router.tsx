import { createBrowserRouter } from 'react-router-dom'

import { AppLayout } from './layouts/AppLayout'
import { DashboardPage } from './pages/DashboardPage'
import { SubredditsPage } from './pages/SubredditsPage'
import { PostsPage } from './pages/PostsPage'
import { AnalysesPage } from './pages/AnalysesPage'
import { TagsPage } from './pages/TagsPage'
import { CrawlerPage } from './pages/CrawlerPage'
import { NotFoundPage } from './pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'subreddits', element: <SubredditsPage /> },
      { path: 'posts', element: <PostsPage /> },
      { path: 'analyses', element: <AnalysesPage /> },
      { path: 'tags', element: <TagsPage /> },
      { path: 'crawler', element: <CrawlerPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

