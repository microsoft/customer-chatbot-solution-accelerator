import { Button, Card, Text } from "@fluentui/react-components";
import { Alert24Regular, ArrowClockwise24Regular } from "@fluentui/react-icons";

export const ErrorFallback = ({ error, resetErrorBoundary }) => {
  if (import.meta.env.DEV) throw error;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="mb-6 p-4 bg-red-50 border-red-200">
          <div className="flex items-center gap-2 mb-2">
            <Alert24Regular className="text-red-600" />
            <Text weight="semibold" className="text-red-800">Application Error</Text>
          </div>
          <Text className="text-red-700">
            Something unexpected happened while running the application. The error details are shown below.
          </Text>
        </Card>
        
        <Card className="p-4 mb-6">
          <Text weight="semibold" size={200} className="text-gray-600 mb-2">Error Details:</Text>
          <pre className="text-xs text-red-600 bg-gray-100 p-3 rounded border overflow-auto max-h-32">
            {error.message}
          </pre>
        </Card>
        
        <Button 
          onClick={resetErrorBoundary} 
          className="w-full"
          appearance="outline"
          icon={<ArrowClockwise24Regular />}
        >
          Try Again
        </Button>
      </div>
    </div>
  );
}
