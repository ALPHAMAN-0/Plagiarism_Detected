/**
 * App router configuration — uses React Router v6 with lazy-loaded routes.
 */

import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { App } from './App';
import { Spinner } from './components/Spinner';

const HomePage = lazy(() => import('./pages/HomePage').then((m) => ({ default: m.HomePage })));
const DetectPage = lazy(() =>
  import('./pages/DetectPage').then((m) => ({ default: m.DetectPage })),
);
const PredictPage = lazy(() =>
  import('./pages/PredictPage').then((m) => ({ default: m.PredictPage })),
);
const CorpusPage = lazy(() =>
  import('./pages/CorpusPage').then((m) => ({ default: m.CorpusPage })),
);
const HistoryPage = lazy(() =>
  import('./pages/HistoryPage').then((m) => ({ default: m.HistoryPage })),
);

function withSuspense(node: React.ReactNode) {
  return <Suspense fallback={<Spinner label="Loading page" />}>{node}</Suspense>;
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: withSuspense(<HomePage />) },
      { path: 'detect', element: withSuspense(<DetectPage />) },
      { path: 'predict', element: withSuspense(<PredictPage />) },
      { path: 'corpus', element: withSuspense(<CorpusPage />) },
      { path: 'history', element: withSuspense(<HistoryPage />) },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
