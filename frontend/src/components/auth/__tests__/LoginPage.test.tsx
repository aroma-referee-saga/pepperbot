import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from '../LoginPage';
import { AuthContext } from '../../../contexts/AuthContext';

// Mock the AuthContext
const mockLogin = vi.fn();
const mockAuthContextValue = {
  user: null,
  login: mockLogin,
  register: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
  isAuthenticated: false,
};

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthContext.Provider value={mockAuthContextValue}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </AuthContext.Provider>
);

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form correctly', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    expect(screen.getByText('Sign in to PepperBot')).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/create a new account/i)).toBeInTheDocument();
  });

  it('updates form data when typing', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'testpass' } });

    expect(usernameInput).toHaveValue('testuser');
    expect(passwordInput).toHaveValue('testpass');
  });

  it('calls login function and navigates on successful login', async () => {
    mockLogin.mockResolvedValueOnce(undefined);

    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'testpass' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'testpass');
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('displays error message on login failure', async () => {
    const errorMessage = 'Invalid credentials';
    mockLogin.mockRejectedValueOnce({
      response: { data: { detail: errorMessage } }
    });

    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('shows loading state during login', async () => {
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);

    expect(screen.getByText('Signing in...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  it('prevents form submission with empty fields', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);

    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('navigates to register page when register link is clicked', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const registerLink = screen.getByText(/create a new account/i);
    fireEvent.click(registerLink);

    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });

  it('handles generic error message when no specific error is provided', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Network error'));

    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Login failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('clears error message when starting new login attempt', async () => {
    mockLogin.mockRejectedValueOnce({
      response: { data: { detail: 'First error' } }
    });

    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // First failed attempt
    fireEvent.click(submitButton);
    await waitFor(() => {
      expect(screen.getByText('First error')).toBeInTheDocument();
    });

    // Second attempt should clear the error
    mockLogin.mockResolvedValueOnce(undefined);
    fireEvent.click(submitButton);
    await waitFor(() => {
      expect(screen.queryByText('First error')).not.toBeInTheDocument();
    });
  });
});