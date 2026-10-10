import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

function Boom(): JSX.Element {
  throw new Error('kapow');
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>ok</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText('ok')).toBeInTheDocument();
  });

  it('renders fallback on error and does not leak stack', () => {
    // Suppress expected React error log
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );
    const fb = screen.getByTestId('error-boundary');
    expect(fb).toBeInTheDocument();
    expect(fb.textContent).toContain('kapow');
    expect(fb.textContent).not.toContain('at ');
    spy.mockRestore();
  });
});
