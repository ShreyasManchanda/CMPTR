import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import './styles/globals.css';
import App from './App.jsx';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 0,
    },
  },
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 5000,
          style: {
            background: 'var(--bg-surface, #1a1a2e)',
            color: 'var(--text-primary, #e8e8ed)',
            border: '1px solid var(--border, rgba(255,255,255,0.08))',
            borderRadius: '12px',
            fontSize: '0.875rem',
          },
          success: {
            iconTheme: {
              primary: '#34d399',
              secondary: '#0a0a14',
            },
          },
          error: {
            iconTheme: {
              primary: '#f87171',
              secondary: '#0a0a14',
            },
            duration: 7000,
          },
        }}
      />
    </QueryClientProvider>
  </StrictMode>,
);
