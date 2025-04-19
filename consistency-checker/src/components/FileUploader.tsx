
import React, { useState, useRef } from 'react';
import { Upload, File, AlertCircle, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface FileUploaderProps {
  accept: string;
  label: string;
  description: string;
  onFileSelect: (file: File) => void;
  maxSizeMB?: number;
}

const FileUploader: React.FC<FileUploaderProps> = ({
  accept,
  label,
  description,
  onFileSelect,
  maxSizeMB = 10
}) => {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    
    if (e.dataTransfer.files.length) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file: File) => {
    setError(null);
    
    // Check if file type is accepted
    if (!file.name.match(new RegExp(accept.split(',').join('|').replace(/\./g, '\\.').replace(/,/g, '$|')))) {
      setError(`Invalid file type. Please upload a ${accept} file.`);
      return;
    }
    
    // Check file size
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File size exceeds ${maxSizeMB}MB.`);
      return;
    }
    
    setSelectedFile(file);
    onFileSelect(file);
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="w-full">
      <div
        className={`file-input-zone ${dragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={triggerFileInput}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept={accept}
          className="hidden"
        />
        <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
        <h3 className="text-lg font-semibold mb-2">{label}</h3>
        <p className="text-sm text-gray-500 mb-4">{description}</p>
        <Button variant="outline" type="button">
          Browse Files
        </Button>
      </div>

      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {selectedFile && !error && (
        <div className="mt-4 p-4 bg-green-50 border border-green-100 rounded-md flex items-center">
          <div className="bg-green-100 p-2 rounded-full">
            <File className="h-5 w-5 text-green-600" />
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-green-900">{selectedFile.name}</p>
            <p className="text-xs text-green-700">{formatFileSize(selectedFile.size)}</p>
          </div>
          <Check className="h-5 w-5 text-green-500" />
        </div>
      )}
    </div>
  );
};

export default FileUploader;
