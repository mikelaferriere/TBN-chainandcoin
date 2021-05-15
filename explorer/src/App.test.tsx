import { render, screen } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/Choose your own adventure/i);
  expect(linkElement).toBeInTheDocument();
});
