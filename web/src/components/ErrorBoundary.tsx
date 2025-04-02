import React, { ErrorInfo } from "react";
import { log } from "../lib/newrelic/NewRelic";
import Error from "../pages/_error";

interface ErrorBoundaryProps {
  children?: React.ReactNode;
}

interface ErrorBoundaryState {
  error?: Error;
  info?: React.ErrorInfo;
}

class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props) {
    super(props);

    this.state = { error: undefined, info: undefined };
  }

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    log(error, JSON.stringify(errorInfo));

    this.setState({
      error,
      info: errorInfo,
    });
  }

  render() {
    const { error } = this.state;

    if (error) {
      return <Error statusCode={error} />;
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
