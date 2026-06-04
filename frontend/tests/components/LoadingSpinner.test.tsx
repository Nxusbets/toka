import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import LoadingSpinner from '../../src/components/common/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default size', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('.loading-spinner');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveStyle({ width: '40px', height: '40px' });
  });

  it('renders with custom size', () => {
    const { container } = render(<LoadingSpinner size={80} />);
    const spinner = container.querySelector('.loading-spinner');
    expect(spinner).toHaveStyle({ width: '80px', height: '80px' });
  });
});
