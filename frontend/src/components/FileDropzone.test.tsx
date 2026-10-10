import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileDropzone } from './FileDropzone';

function makeFile(name: string, sizeBytes: number, type: string): File {
  const content = new Uint8Array(sizeBytes);
  return new File([content], name, { type });
}

describe('FileDropzone', () => {
  it('accepts a .txt file via drop', async () => {
    const onFile = vi.fn();
    render(<FileDropzone onFile={onFile} />);
    const file = makeFile('hello.txt', 100, 'text/plain');
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    await userEvent.upload(input, file);
    await waitFor(() => expect(onFile).toHaveBeenCalledWith(file));
  });

  it('rejects a disallowed extension', async () => {
    const onFile = vi.fn();
    render(<FileDropzone onFile={onFile} />);
    const file = makeFile('evil.exe', 100, 'application/octet-stream');
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    // react-dropzone with `accept` blocks non-matching types at the input level.
    Object.defineProperty(input, 'files', { value: [file] });
    fireEvent.change(input);
    expect(onFile).not.toHaveBeenCalled();
  });

  it('rejects files larger than 10 MB', async () => {
    const onFile = vi.fn();
    render(<FileDropzone onFile={onFile} />);
    const big = makeFile('big.txt', 11 * 1024 * 1024, 'text/plain');
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    Object.defineProperty(input, 'files', { value: [big] });
    fireEvent.change(input);
    expect(onFile).not.toHaveBeenCalled();
  });

  it('disables interaction when disabled', () => {
    render(<FileDropzone onFile={() => {}} disabled />);
    const zone = screen.getByTestId('file-dropzone');
    expect(zone.className).toContain('dropzone--disabled');
    expect(zone).toHaveAttribute('aria-disabled', 'true');
  });
});
