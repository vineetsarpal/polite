import { Provider } from "@/components/ui/provider"
import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { AuthProvider } from "./context/AuthContext"
// import { Auth0Provider } from '@auth0/auth0-react'

import { routeTree } from './routeTree.gen'


const queryClient = new QueryClient()

const router = createRouter({ 
  routeTree,
  context: {
    queryClient,
  },
  defaultPreload: 'intent',
  defaultPreloadStaleTime: 0,
  scrollRestoration: true,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

const rootElement = document.getElementById('root')!
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <StrictMode>
      <Provider>
        <QueryClientProvider client={queryClient}>
          {/* <Auth0Provider
              domain={import.meta.env.VITE_AUTH0_DOMAIN}
              clientId={import.meta.env.VITE_AUTH0_CLIENT_ID}
              authorizationParams={{
                redirect_uri: import.meta.env.VITE_AUTH0_CALLBACK_URL,
                audience: import.meta.env.VITE_AUTH0_AUDIENCE,
              }}
          > */}
            <AuthProvider>
              <RouterProvider router={router} />
              <ReactQueryDevtools initialIsOpen={false} />
            </AuthProvider>
          {/* </Auth0Provider> */}
        </QueryClientProvider>
      </Provider>
    </StrictMode>,
  )
}