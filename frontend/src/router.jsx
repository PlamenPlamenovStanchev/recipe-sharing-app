import { createBrowserRouter } from 'react-router'
import { ProtectedRoute } from './auth/ProtectedRoute.jsx'
import { RoleRoute } from './auth/RoleRoute.jsx'
import { AppLayout } from './layouts/AppLayout.jsx'
import { CreateRecipePage } from './pages/CreateRecipePage.jsx'
import { HomePage } from './pages/HomePage.jsx'
import { LoginPage } from './pages/LoginPage.jsx'
import { NotFoundPage } from './pages/NotFoundPage.jsx'
import { RecipesPage } from './pages/RecipesPage.jsx'
import { RegisterPage } from './pages/RegisterPage.jsx'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'recipes', element: <RecipesPage /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <RoleRoute allowedRoles={['USER', 'MODERATOR', 'ADMIN']} />,
            children: [
              { path: 'recipes/new', element: <CreateRecipePage /> },
            ],
          },
        ],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
