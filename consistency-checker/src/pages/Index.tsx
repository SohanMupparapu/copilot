import React, { useState } from 'react';
import { FileText, FileCode, Beaker, Cog, Lightbulb, FileCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from '@/components/ui/use-toast';
import FileUploader from '@/components/FileUploader';
import ServiceCard from '@/components/ServiceCard';
import ResultsDisplay from '@/components/ResultsDisplay';
import ConsistencyChecker from '@/components/ConsistencyChecker';

// Combine both components into one
export default function Home() {
  // State from TestPortal component
  const [reqDocument, setReqDocument] = useState<File | null>(null);
  const [codebaseFiles, setCodebaseFiles] = useState<File | null>(null);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');
  const [activeTab, setActiveTab] = useState('upload');
  const [results, setResults] = useState<any>(null);

  const handleFileSelect = (type: 'requirements' | 'codebase', file: File) => {
    if (type === 'requirements') {
      setReqDocument(file);
    } else {
      setCodebaseFiles(file);
    }
  };

  const handleServiceSelect = (service: string) => {
    setSelectedService(service);
  };

  const handleProcessFiles = async () => {
    if (!reqDocument || !codebaseFiles || !selectedService) {
      toast({
        title: "Missing Information",
        description: "Please upload all required files and select a service.",
        variant: "destructive"
      });
      return;
    }

    setProcessingStatus('processing');
    setActiveTab('results');
    
    try {
      // Simulate API call to the selected microservice
      const analysisResults = await simulateAnalysis(selectedService);
      setResults(analysisResults);
      setProcessingStatus('completed');
      toast({
        title: "Analysis Complete",
        description: "Your files have been successfully analyzed.",
      });
    } catch (error) {
      setProcessingStatus('error');
      toast({
        title: "Analysis Failed",
        description: "There was an error processing your files.",
        variant: "destructive"
      });
    }
  };

  const handleDownloadResults = () => {
    // Simulate downloading results as a PDF or JSON file
    toast({
      title: "Download Started",
      description: "Your report is being prepared for download.",
    });
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8">
      <div className="w-full max-w-5xl">
        <h1 className="text-3xl font-bold mb-8 text-center">CoPilot for Test Case Generation</h1>
        
        <Tabs defaultValue="testgen" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="testgen">Test Case Generation</TabsTrigger>
            <TabsTrigger value="consistency">Consistency Checker</TabsTrigger>
          </TabsList>
          
          <TabsContent value="testgen">
            {/* Test Portal UI */}
            <div className="min-h-screen bg-gray-50">
              <header className="bg-white border-b border-gray-200">
                <div className="container mx-auto px-4 py-4">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <Beaker className="h-6 w-6 text-primary mr-2" />
                      <h1 className="text-xl font-bold text-gray-900">Test Case Portal</h1>
                    </div>
                    <div>
                      <Button variant="outline" size="sm" className="mr-2">
                        <Cog className="h-4 w-4 mr-1" />
                        Settings
                      </Button>
                      <Button size="sm">
                        <FileCheck className="h-4 w-4 mr-1" />
                        View Reports
                      </Button>
                    </div>
                  </div>
                </div>
              </header>

              <main className="container mx-auto px-4 py-8">
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="mb-8">
                    <TabsTrigger value="upload">Upload Files</TabsTrigger>
                    <TabsTrigger value="service">Select Service</TabsTrigger>
                    <TabsTrigger value="results">View Results</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="upload" className="animate-fade-in">
                    <div className="grid md:grid-cols-2 gap-8">
                      <div>
                        <FileUploader
                          accept=".pdf,.doc,.docx,.txt"
                          label="Upload Requirements Document"
                          description="Drag and drop your SRS document, or click to browse"
                          onFileSelect={(file) => handleFileSelect('requirements', file)}
                        />
                      </div>
                      <div>
                        <FileUploader
                          accept=".zip,.rar,.tar,.gz,.jar,.java"
                          label="Upload Codebase Files"
                          description="Drag and drop your codebase archive, or click to browse"
                          onFileSelect={(file) => handleFileSelect('codebase', file)}
                        />
                      </div>
                    </div>
                    
                    <div className="mt-8 flex justify-end">
                      <Button
                        onClick={() => setActiveTab('service')}
                        disabled={!reqDocument || !codebaseFiles}
                      >
                        Continue to Service Selection
                      </Button>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="service" className="animate-fade-in">
                    <div className="mb-6">
                      <h2 className="text-xl font-bold mb-2">Select Microservice</h2>
                      <p className="text-gray-600">Choose one of our microservices to process your files</p>
                    </div>
                    
                    <div className="grid md:grid-cols-3 gap-6">
                      <ServiceCard
                        title="Test Case Generation"
                        description="Create test cases based on your requirements document and codebase"
                        icon={<FileText className="h-5 w-5" />}
                        onSelect={() => handleServiceSelect('testCaseGeneration')}
                        isSelected={selectedService === 'testCaseGeneration'}
                      />
                      <ServiceCard
                        title="SRS Document Consistency"
                        description="Check consistency between your requirements and implementation"
                        icon={<FileCode className="h-5 w-5" />}
                        onSelect={() => handleServiceSelect('docConsistency')}
                        isSelected={selectedService === 'docConsistency'}
                      />
                      <ServiceCard
                        title="Test Scenario Generator"
                        description="Generate comprehensive test scenarios for your application"
                        icon={<Lightbulb className="h-5 w-5" />}
                        onSelect={() => handleServiceSelect('scenarioGenerator')}
                        isSelected={selectedService === 'scenarioGenerator'}
                      />
                    </div>
                    
                    <div className="mt-8 flex justify-between">
                      <Button variant="outline" onClick={() => setActiveTab('upload')}>
                        Back to File Upload
                      </Button>
                      <Button 
                        onClick={handleProcessFiles}
                        disabled={!selectedService}
                      >
                        Process Files
                      </Button>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="results" className="animate-fade-in">
                    <div className="mb-6">
                      <h2 className="text-xl font-bold mb-2">Analysis Results</h2>
                      <p className="text-gray-600">
                        {processingStatus === 'processing' 
                          ? 'Processing your files, this may take a few moments...' 
                          : 'Review the analysis results below'}
                      </p>
                    </div>
                    
                    <ResultsDisplay
                      title={results?.title || 'Processing Results'}
                      summary={results?.summary || { total: 0, passed: 0, failed: 0, warnings: 0 }}
                      testCases={results?.testCases || []}
                      onDownload={handleDownloadResults}
                      isLoading={processingStatus === 'processing'}
                    />
                    
                    <div className="mt-8 flex justify-between">
                      <Button variant="outline" onClick={() => setActiveTab('service')}>
                        Back to Service Selection
                      </Button>
                      {processingStatus === 'completed' && (
                        <Button onClick={() => {
                          setActiveTab('upload');
                          setReqDocument(null);
                          setCodebaseFiles(null);
                          setSelectedService(null);
                          setProcessingStatus('idle');
                          setResults(null);
                        }}>
                          Start New Analysis
                        </Button>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </main>
              
              <footer className="bg-white border-t border-gray-200 mt-12">
                <div className="container mx-auto px-4 py-6">
                  <div className="text-center text-gray-500 text-sm">
                    <p>Test Case Portal - Java Microservices Integration</p>
                    <p className="mt-1">© 2025 Your Company</p>
                  </div>
                </div>
              </footer>
            </div>
          </TabsContent>
          
          <TabsContent value="consistency">
            <ConsistencyChecker />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}

// Simulate microservice integration
const simulateAnalysis = (serviceType: string): Promise<any> => {
  return new Promise((resolve) => {
    // Simulate API call delay
    setTimeout(() => {
      // Mock test case results
      const mockResults = {
        testCaseGeneration: {
          title: 'Test Case Generation Results',
          summary: { total: 18, passed: 15, failed: 2, warnings: 1 },
          testCases: [
            {
              id: '1',
              name: 'Login Authentication Test',
              description: 'Verifies user login with valid credentials',
              status: 'pass',
              details: 'Test successfully generated.\n\nPrecondition: User account exists\nSteps:\n1. Navigate to login page\n2. Enter valid username\n3. Enter valid password\n4. Click submit button\nExpected Result: User is logged in and redirected to dashboard'
            },
            {
              id: '2',
              name: 'Password Reset Flow',
              description: 'Validates the password reset functionality',
              status: 'pass',
              details: 'Test successfully generated.\n\nPrecondition: User has an account\nSteps:\n1. Click "Forgot Password"\n2. Enter email address\n3. Check email and click reset link\n4. Enter new password\n5. Confirm new password\nExpected Result: Password is changed and user can login with new credentials'
            },
            {
              id: '3',
              name: 'User Registration',
              description: 'Tests the new user registration process',
              status: 'fail',
              details: 'Failed to generate complete test case. Missing field validations from requirements document.\n\nError: Unable to determine password requirements from SRS document.'
            },
            {
              id: '4',
              name: 'Admin Report Generation',
              description: 'Tests admin ability to generate usage reports',
              status: 'warning',
              details: 'Test case generated with warnings.\n\nWarning: The permission model is not clearly defined in requirements. Assuming admin has full access.'
            }
          ]
        },
        docConsistency: {
          title: 'SRS Document Consistency Check',
          summary: { total: 12, passed: 9, failed: 2, warnings: 1 },
          testCases: [
            {
              id: '1',
              name: 'Requirement FR-101',
              description: 'User login functionality',
              status: 'pass',
              details: 'Requirement is consistent with implementation in codebase.'
            },
            {
              id: '2',
              name: 'Requirement FR-102',
              description: 'User logout functionality',
              status: 'pass',
              details: 'Requirement is consistent with implementation in codebase.'
            },
            {
              id: '3',
              name: 'Requirement FR-103',
              description: 'Password complexity requirements',
              status: 'fail',
              details: 'Inconsistency found: SRS requires minimum 10 characters but implementation enforces only 8 characters.'
            },
            {
              id: '4',
              name: 'Requirement NFR-201',
              description: 'System response time',
              status: 'warning',
              details: 'Partial consistency: Performance requirements stated in SRS but not fully testable in current implementation.'
            }
          ]
        },
        scenarioGenerator: {
          title: 'Test Scenario Generation Results',
          summary: { total: 10, passed: 8, failed: 1, warnings: 1 },
          testCases: [
            {
              id: '1',
              name: 'End-to-End User Registration Flow',
              description: 'Full user registration journey',
              status: 'pass',
              details: 'Successfully generated test scenario with 7 test cases covering the complete user registration flow.'
            },
            {
              id: '2',
              name: 'E-commerce Checkout Process',
              description: 'Complete checkout and payment flow',
              status: 'pass',
              details: 'Generated test scenario with 5 test cases for the checkout process including payment verification.'
            },
            {
              id: '3',
              name: 'Data Migration Process',
              description: 'Legacy data migration flow',
              status: 'fail',
              details: 'Failed to generate test scenario. Implementation details in codebase do not match requirements specification.'
            },
            {
              id: '4',
              name: 'Multi-user Collaboration',
              description: 'Simultaneous document editing',
              status: 'warning',
              details: 'Generated scenario with warnings. Race condition handling not clearly defined in requirements.'
            }
          ]
        }
      };
      
      return resolve(mockResults[serviceType as keyof typeof mockResults]);
    }, 2000);
  });
};
