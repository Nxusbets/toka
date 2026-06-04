import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DataTable from '../../src/components/common/DataTable';
import type { Column } from '../../src/components/common/DataTable';

interface TestItem {
  id: string;
  name: string;
}

const columns: Column<TestItem>[] = [
  { key: 'id', header: 'ID', render: (item) => item.id },
  { key: 'name', header: 'Name', render: (item) => item.name },
];

const data: TestItem[] = [
  { id: '1', name: 'Alice' },
  { id: '2', name: 'Bob' },
];

describe('DataTable', () => {
  it('renders table with data', () => {
    render(<DataTable columns={columns} data={data} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('ID')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
  });

  it('shows loading skeleton when loading is true', () => {
    const { container } = render(
      <DataTable columns={columns} data={[]} loading />,
    );
    expect(container.querySelector('.skeleton')).toBeInTheDocument();
  });

  it('shows EmptyState when data is empty', () => {
    render(<DataTable columns={columns} data={[]} />);
    expect(screen.getByText('No data found')).toBeInTheDocument();
  });

  it('shows custom empty message when data is empty', () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        emptyMessage="Nothing here"
      />,
    );
    expect(screen.getByText('Nothing here')).toBeInTheDocument();
  });

  it('shows error state when error is set', () => {
    render(
      <DataTable columns={columns} data={[]} error="Something broke" />,
    );
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });

  it('shows retry button in error state when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(
      <DataTable
        columns={columns}
        data={[]}
        error="Error"
        onRetry={onRetry}
      />,
    );
    const button = screen.getByRole('button', { name: 'Retry' });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('calls onPageChange when pagination buttons are clicked', () => {
    const onPageChange = vi.fn();
    const { container } = render(
      <DataTable
        columns={columns}
        data={data}
        page={1}
        total={40}
        size={20}
        onPageChange={onPageChange}
      />,
    );
    const buttons = container.querySelectorAll('.pagination button');
    const nextButton = buttons[1];
    fireEvent.click(nextButton);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('disables previous button on first page', () => {
    const { container } = render(
      <DataTable
        columns={columns}
        data={data}
        page={1}
        total={40}
        size={20}
        onPageChange={vi.fn()}
      />,
    );
    const buttons = container.querySelectorAll('.pagination button');
    expect(buttons[0]).toBeDisabled();
  });

  it('disables next button on last page', () => {
    const { container } = render(
      <DataTable
        columns={columns}
        data={data}
        page={2}
        total={40}
        size={20}
        onPageChange={vi.fn()}
      />,
    );
    const buttons = container.querySelectorAll('.pagination button');
    expect(buttons[1]).toBeDisabled();
  });
});
