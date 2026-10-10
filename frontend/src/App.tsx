/**
 * App — top-level layout: header + nav + outlet for routes.
 */

import { NavLink, Outlet } from 'react-router-dom';
import { ErrorBoundary } from './components/ErrorBoundary';

export function App() {
  return (
    <ErrorBoundary>
      <div className="app">
        <header className="app__header">
          <NavLink to="/" className="app__brand" data-testid="brand">
            Plagiarism_Detected
          </NavLink>
          <nav className="app__nav" aria-label="Main">
            <NavLink to="/detect" data-testid="nav-detect">
              Detect
            </NavLink>
            <NavLink to="/predict" data-testid="nav-predict">
              Predict
            </NavLink>
            <NavLink to="/corpus" data-testid="nav-corpus">
              Corpus
            </NavLink>
            <NavLink to="/history" data-testid="nav-history">
              History
            </NavLink>
          </nav>
        </header>
        <Outlet />
      </div>
    </ErrorBoundary>
  );
}
