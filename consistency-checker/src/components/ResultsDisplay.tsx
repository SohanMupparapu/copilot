
import React from 'react';
import { Check, AlertTriangle, X, Download, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';

interface TestCase {
  id: string;
  name: string;
  description: string;
  status: 'pass' | 'fail' | 'warning';
  details?: string;
}

interface ResultsDisplayProps {
  title: string;
  summary: {
    total: number;
    passed: number;
    failed: number;
    warnings: number;
  };
  testCases: TestCase[];
  onDownload?: () => void;
  isLoading: boolean;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  title,
  summary,
  testCases,
  onDownload,
  isLoading
}) => {
  if (isLoading) {
    return (
      <Card className="w-full animate-pulse">
        <CardHeader>
          <div className="h-7 bg-gray-200 rounded-md w-1/3 mb-3"></div>
          <div className="h-5 bg-gray-200 rounded-md w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-gray-100 rounded-md"></div>
        </CardContent>
      </Card>
    );
  }

  const getStatusIcon = (status: 'pass' | 'fail' | 'warning') => {
    switch (status) {
      case 'pass':
        return <Check className="h-5 w-5 text-green-500" />;
      case 'fail':
        return <X className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-amber-500" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>{title}</CardTitle>
          <div className="flex space-x-4 mt-2">
            <div className="flex items-center">
              <div className="h-3 w-3 rounded-full bg-green-500 mr-1"></div>
              <span className="text-sm">{summary.passed} Passed</span>
            </div>
            <div className="flex items-center">
              <div className="h-3 w-3 rounded-full bg-red-500 mr-1"></div>
              <span className="text-sm">{summary.failed} Failed</span>
            </div>
            <div className="flex items-center">
              <div className="h-3 w-3 rounded-full bg-amber-500 mr-1"></div>
              <span className="text-sm">{summary.warnings} Warnings</span>
            </div>
          </div>
        </div>
        {onDownload && (
          <Button variant="outline" size="sm" onClick={onDownload}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="all">
          <TabsList className="mb-4">
            <TabsTrigger value="all">All ({summary.total})</TabsTrigger>
            <TabsTrigger value="passed">Passed ({summary.passed})</TabsTrigger>
            <TabsTrigger value="failed">Failed ({summary.failed})</TabsTrigger>
            <TabsTrigger value="warnings">Warnings ({summary.warnings})</TabsTrigger>
          </TabsList>
          
          <TabsContent value="all">
            <ScrollArea className="h-[400px]">
              {testCases.map((testCase) => (
                <TestCaseItem key={testCase.id} testCase={testCase} />
              ))}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="passed">
            <ScrollArea className="h-[400px]">
              {testCases.filter(tc => tc.status === 'pass').map((testCase) => (
                <TestCaseItem key={testCase.id} testCase={testCase} />
              ))}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="failed">
            <ScrollArea className="h-[400px]">
              {testCases.filter(tc => tc.status === 'fail').map((testCase) => (
                <TestCaseItem key={testCase.id} testCase={testCase} />
              ))}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="warnings">
            <ScrollArea className="h-[400px]">
              {testCases.filter(tc => tc.status === 'warning').map((testCase) => (
                <TestCaseItem key={testCase.id} testCase={testCase} />
              ))}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

const TestCaseItem: React.FC<{ testCase: TestCase }> = ({ testCase }) => {
  const [expanded, setExpanded] = React.useState(false);
  
  return (
    <div className={`p-4 border rounded-md mb-2 ${
      testCase.status === 'pass' ? 'bg-green-50 border-green-100' : 
      testCase.status === 'fail' ? 'bg-red-50 border-red-100' : 
      'bg-amber-50 border-amber-100'
    }`}>
      <div className="flex items-start">
        <div className="mt-1">
          {getStatusIcon(testCase.status)}
        </div>
        <div className="ml-3 flex-1">
          <div className="flex justify-between">
            <h4 className="font-medium">{testCase.name}</h4>
            <button 
              className="text-gray-600 text-sm hover:text-gray-900" 
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Hide Details' : 'Show Details'}
            </button>
          </div>
          <p className="text-sm text-gray-600">{testCase.description}</p>
          
          {expanded && testCase.details && (
            <div className="mt-3 p-3 bg-white rounded border text-sm font-mono whitespace-pre-wrap">
              {testCase.details}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultsDisplay;
