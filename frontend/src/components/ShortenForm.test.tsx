import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import { ShortenForm } from './ShortenForm';

const link = {
  id: '1', short_url: 'https://sho.rt/demo', short_code: 'demo',
  original_url: 'https://example.com', title: null, custom_alias: null,
  is_active: true, expires_at: null, created_at: '', updated_at: '', total_clicks: 0,
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true, status: 201, json: () => Promise.resolve(link),
  }));
});

async function shortenLink() {
  render(<ShortenForm />);
  fireEvent.change(screen.getByLabelText('Long URL'), { target: { value: link.original_url } });
  fireEvent.click(screen.getByRole('button', { name: 'Shorten link' }));
  await screen.findByText(link.short_url);
}

test('submits a URL and displays the returned short link', async () => {
  await shortenLink();
  expect(screen.getByText(link.short_url)).toBeInTheDocument();
});

test('copies the short URL and announces success', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
  await shortenLink();
  fireEvent.click(screen.getByRole('button', { name: 'Copy short URL' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Short URL copied to clipboard');
  expect(writeText).toHaveBeenCalledWith(link.short_url);
  expect(screen.getByRole('button', { name: 'Copied short URL' })).toBeInTheDocument();
});

test('announces clipboard failures', async () => {
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText: vi.fn().mockRejectedValue(new Error('blocked')) },
  });
  await shortenLink();
  fireEvent.click(screen.getByRole('button', { name: 'Copy short URL' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Unable to copy short URL');
});
