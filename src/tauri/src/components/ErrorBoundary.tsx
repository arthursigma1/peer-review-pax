import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen flex items-center justify-center bg-zinc-950 text-zinc-100 p-8">
          <div className="max-w-lg space-y-4">
            <h1 className="text-xl font-semibold text-red-400">UI Error</h1>
            <pre className="text-xs text-zinc-400 bg-zinc-900 p-4 rounded overflow-auto max-h-60">
              {this.state.error?.message}
              {"\n"}
              {this.state.error?.stack}
            </pre>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 rounded bg-teal-600 hover:bg-teal-500 text-sm font-medium"
            >
              Try to Recover
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
