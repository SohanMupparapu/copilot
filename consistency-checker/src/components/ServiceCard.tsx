
import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ServiceCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  status?: 'idle' | 'processing' | 'completed' | 'error';
  onSelect: () => void;
  isSelected: boolean;
}

const ServiceCard: React.FC<ServiceCardProps> = ({
  title,
  description,
  icon,
  status = 'idle',
  onSelect,
  isSelected
}) => {
  const getStatusBadge = () => {
    switch (status) {
      case 'processing':
        return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">Processing</Badge>;
      case 'completed':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Completed</Badge>;
      case 'error':
        return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Error</Badge>;
      default:
        return <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">Ready</Badge>;
    }
  };

  return (
    <Card className={`service-card ${isSelected ? 'ring-2 ring-primary' : ''}`}>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center text-primary">
            {icon}
          </div>
          {getStatusBadge()}
        </div>
        <CardTitle className="mt-4">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Service-specific content could go here */}
      </CardContent>
      <CardFooter>
        <Button 
          onClick={onSelect} 
          variant={isSelected ? "default" : "outline"} 
          className="w-full"
        >
          {isSelected ? 'Selected' : 'Select Service'}
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ServiceCard;
