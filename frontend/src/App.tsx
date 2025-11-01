import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import BloggersPage from './pages/BloggersPage'
import CreatePage from './pages/CreatePage'
import ProjectsPage from './pages/ProjectsPage'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/bloggers" replace />} />
            <Route path="/bloggers" element={<BloggersPage />} />
            <Route path="/create" element={<CreatePage />} />
            <Route path="/projects" element={<ProjectsPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
