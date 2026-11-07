import { afterEach, describe, it, expect, vi } from 'vitest';
import { cleanup, render, screen, fireEvent } from '@testing-library/react';
import { useState } from 'react';
import { Modal } from './Modal';

afterEach(() => {
  cleanup();
});

describe('Modal component focus and stability', () => {
  it('does not steal focus back to close button when input text changes and parent re-renders', () => {
    const TestComponent = () => {
      const [isOpen, setIsOpen] = useState(true);
      const [text, setText] = useState('');

      return (
        <Modal
          isOpen={isOpen}
          // Intentionally inline anonymous function recreated on each re-render
          onClose={() => setIsOpen(false)}
          title="Test Modal"
        >
          <input
            data-testid="test-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </Modal>
      );
    };

    render(<TestComponent />);
    const input = screen.getByTestId('test-input');
    const closeBtn = screen.getByRole('button', { name: 'Close modal' });

    // Focus input
    input.focus();
    expect(document.activeElement).toBe(input);

    // Type consecutive characters
    fireEvent.change(input, { target: { value: 'a' } });
    expect(document.activeElement).toBe(input);
    expect(document.activeElement).not.toBe(closeBtn);

    fireEvent.change(input, { target: { value: 'ab' } });
    expect(document.activeElement).toBe(input);
    expect(document.activeElement).not.toBe(closeBtn);

    fireEvent.change(input, { target: { value: 'abc' } });
    expect(document.activeElement).toBe(input);
    expect(document.activeElement).not.toBe(closeBtn);
    expect((input as HTMLInputElement).value).toBe('abc');
  });

  it('close button has type="button" and closes modal only when clicked', () => {
    const handleClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={handleClose} title="Test Modal">
        <div>Modal Content</div>
      </Modal>
    );

    const closeBtn = screen.getByRole('button', { name: 'Close modal' });
    expect(closeBtn.getAttribute('type')).toBe('button');

    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
