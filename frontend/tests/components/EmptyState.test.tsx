import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import EmptyState from '../../src/components/common/EmptyState';

describe('EmptyState', () => {
  it('renders default message', () => {
    render(<EmptyState />);
    expect(screen.getByText('No data found')).toBeInTheDocument();
  });

  it('renders custom message', () => {
    render(<EmptyState message="No users found" />);
    expect(screen.getByText('No users found')).toBeInTheDocument();
  });

  it('renders icon', () => {
    const { container } = render(<EmptyState />);
    expect(container.querySelector('.empty-state-icon')).toBeInTheDocument();
  });

  it('renders action button when actionLabel and onAction are provided', () => {
    const onAction = vi.fn();
    render(<EmptyState actionLabel="Add User" onAction={onAction} />);
    const button = screen.getByRole('button', { name: 'Add User' });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('does not render action button when onAction is missing', () => {
    render(<EmptyState actionLabel="Add User" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
