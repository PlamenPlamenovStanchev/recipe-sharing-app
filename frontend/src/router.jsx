import { createBrowserRouter } from 'react-router'
import { ProtectedRoute } from './auth/ProtectedRoute.jsx'
import { RoleRoute } from './auth/RoleRoute.jsx'
import { AppLayout } from './layouts/AppLayout.jsx'
import { AdminPage } from './pages/AdminPage.jsx'
import { CreateRecipePage } from './pages/CreateRecipePage.jsx'
import { EditRecipePage } from './pages/EditRecipePage.jsx'
import { HomePage } from './pages/HomePage.jsx'
import { LoginPage } from './pages/LoginPage.jsx'
import { ModeratorPage } from './pages/ModeratorPage.jsx'
import { NotFoundPage } from './pages/NotFoundPage.jsx'
import { RecipesPage } from './pages/RecipesPage.jsx'
import { RecipeDetailsPage } from './pages/RecipeDetailsPage.jsx'
import { RegisterPage } from './pages/RegisterPage.jsx'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'recipes', element: <RecipesPage /> },
      { path: 'recipes/:recipeId', element: <RecipeDetailsPage /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <RoleRoute allowedRoles={['USER', 'MODERATOR', 'ADMIN']} />,
            children: [
              { path: 'recipes/new', element: <CreateRecipePage /> },
              { path: 'recipes/:recipeId/edit', element: <EditRecipePage /> },
            ],
          },
          {
            element: <RoleRoute allowedRoles={['MODERATOR', 'ADMIN']} />,
            children: [
              { path: 'moderator', element: <ModeratorPage /> },
            ],
          },
          {
            element: <RoleRoute allowedRoles={['ADMIN']} />,
            children: [
              { path: 'admin', element: <AdminPage /> },
            ],
          },
        ],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
