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
        <div className="h-screen flex items-center justify-center bg-white text-gray-900 p-8">
          <div className="max-w-lg space-y-4">
            <h1 className="text-xl font-semibold text-red-600">UI Error</h1>
            <pre className="text-xs text-gray-600 bg-gray-50 p-4 rounded overflow-auto max-h-60">
              {this.state.error?.message}
              {"\n"}
              {this.state.error?.stack}
            </pre>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 rounded bg-[#0068ff] hover:bg-[#0055d4] text-white text-sm font-medium"
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
