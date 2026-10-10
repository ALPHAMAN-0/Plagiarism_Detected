/**
 * ErrorBoundary — top-level React error boundary.
 * Renders a friendly fallback; never leaks stack traces to the UI.
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(err: Error): State {
    return { hasError: true, message: err.message || 'Something went wrong' };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Log to console only — do not echo to UI.
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught', error, info);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="error-boundary" role="alert" data-testid="error-boundary">
          <h1>Something went wrong</h1>
          <p>{this.state.message}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
