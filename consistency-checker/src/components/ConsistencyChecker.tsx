import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, FileText, Upload, Check } from "lucide-react";

const ConsistencyChecker: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setIsComplete(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError("Please select a file first");
      return;
    }

    setIsUploading(true);
    setIsProcessing(true);
    setError(null);
    
    // In the handleSubmit function, update the response handling:
try {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('http://localhost:5000/api/check-consistency', {
    method: 'POST',
    body: formData,
    mode: 'cors',
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to process requirements');
  }

  // Check the content type of the response
  const contentType = response.headers.get('content-type');
  
  if (contentType && contentType.includes('application/pdf')) {
    // Handle PDF response
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    
    // Create a link and trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = 'requirements_analysis_report.pdf';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  } else {
    // Handle JSON response (fallback if PDF generation failed)
    const jsonData = await response.json();
    
    // Display the markdown report
    if (jsonData.report) {
      // You could add state to display this in the UI
      console.log("Received markdown report:", jsonData.report);
      
      // Create a text file download
      const blob = new Blob([jsonData.report], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = 'requirements_analysis_report.md';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    }
  }
  
  setIsComplete(true);
} catch (err) {
  setError(err instanceof Error ? err.message : 'An unknown error occurred');
} finally {
  setIsUploading(false);
  setIsProcessing(false);
}

  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>Requirements Consistency Checker</CardTitle>
        <CardDescription>
          Upload a requirements document to check for inconsistencies and generate a PDF report.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <div className="flex items-center justify-center w-full">
                <label htmlFor="file-upload" className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-8 h-8 mb-3 text-gray-500" />
                    <p className="mb-2 text-sm text-gray-500">
                      <span className="font-semibold">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-gray-500">TXT, PDF, DOCX (MAX. 10MB)</p>
                  </div>
                  <Input 
                    id="file-upload" 
                    type="file" 
                    className="hidden" 
                    onChange={handleFileChange}
                    accept=".txt,.pdf,.docx,.doc"
                  />
                </label>
              </div>
              {file && (
                <div className="flex items-center mt-2 text-sm">
                  <FileText className="w-4 h-4 mr-2" />
                  <span>{file.name}</span>
                </div>
              )}
            </div>
          </div>
          
          <Button 
            type="submit" 
            className="w-full mt-4" 
            disabled={!file || isUploading || isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Check Consistency & Generate Report'}
          </Button>
        </form>

        {error && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {isComplete && (
          <Alert className="mt-4 bg-green-50 border-green-200">
            <Check className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-800">Success!</AlertTitle>
            <AlertDescription className="text-green-700">
              Your requirements have been analyzed and the report has been downloaded.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter>
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="about">
            <AccordionTrigger>About the Consistency Checker</AccordionTrigger>
            <AccordionContent>
              <p className="text-sm text-gray-600">
                The Requirements Consistency Checker analyzes your requirements document to identify 
                contradictions, ambiguities, or conflicts between requirements. It uses advanced 
                natural language processing to detect potential issues and provides suggestions for 
                resolution. The generated PDF report includes detailed findings and recommendations.
              </p>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardFooter>
    </Card>
  );
};

export default ConsistencyChecker;
