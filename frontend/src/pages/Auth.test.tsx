import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { request } from '../lib/api';
import { Auth } from './Auth';

vi.mock('../lib/api', () => ({ request: vi.fn() }));

test('prevents duplicate submissions and allows retry after failure', async () => {
  let rejectRequest!: (reason: Error) => void;
  vi.mocked(request).mockReturnValue(new Promise((_, reject) => { rejectRequest = reject; }));
  render(<MemoryRouter><Auth mode="login" /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'student@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
  const form = screen.getByRole('button', { name: 'Log in' }).closest('form')!;
  fireEvent.submit(form);
  fireEvent.submit(form);
  expect(request).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('button', { name: 'Logging in…' })).toBeDisabled();
  rejectRequest(new Error('Please try again'));
  expect(await screen.findByRole('alert')).toHaveTextContent('Please try again');
  await waitFor(() => expect(screen.getByRole('button', { name: 'Log in' })).toBeEnabled());
});
