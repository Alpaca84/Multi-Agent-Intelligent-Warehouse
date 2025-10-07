import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Divider,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Search as SearchIcon,
  Assessment as AnalyticsIcon,
  CheckCircle as ApprovedIcon,
  Warning as ReviewIcon,
  Error as RejectedIcon,
  Description as DocumentIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  CheckCircle,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface DocumentProcessingStage {
  name: string;
  completed: boolean;
  current: boolean;
  description: string;
}

interface DocumentItem {
  id: string;
  filename: string;
  status: string;
  uploadTime: Date;
  progress: number;
  stages: DocumentProcessingStage[];
}

const DocumentExtraction: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [uploadedDocuments, setUploadedDocuments] = useState<DocumentItem[]>([]);
  const [processingDocuments, setProcessingDocuments] = useState<DocumentItem[]>([]);
  const [completedDocuments, setCompletedDocuments] = useState<DocumentItem[]>([]);
  const navigate = useNavigate();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleDocumentUpload = async (file: File) => {
    try {
      // Mock document upload
      const documentId = `doc-${Date.now()}`;
      const newDocument: DocumentItem = {
        id: documentId,
        filename: file.name,
        status: 'processing',
        uploadTime: new Date(),
        progress: 0,
        stages: [
          { name: 'Preprocessing', completed: false, current: true, description: 'Document preprocessing with NeMo Retriever' },
          { name: 'OCR Extraction', completed: false, current: false, description: 'Intelligent OCR with NeMoRetriever-OCR-v1' },
          { name: 'LLM Processing', completed: false, current: false, description: 'Small LLM processing with Llama Nemotron Nano VL 8B' },
          { name: 'Validation', completed: false, current: false, description: 'Large LLM judge and validator' },
          { name: 'Routing', completed: false, current: false, description: 'Intelligent routing based on quality scores' },
        ]
      };
      
      setProcessingDocuments(prev => [...prev, newDocument]);
      
      // Simulate processing
      simulateDocumentProcessing(documentId);
      
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const simulateDocumentProcessing = (documentId: string) => {
    const stages = [
      { name: 'Preprocessing', duration: 2000 },
      { name: 'OCR Extraction', duration: 3000 },
      { name: 'LLM Processing', duration: 4000 },
      { name: 'Validation', duration: 2000 },
      { name: 'Routing', duration: 1000 },
    ];

    let currentStage = 0;
    let progress = 0;

    const processStage = () => {
      if (currentStage < stages.length) {
        const stage = stages[currentStage];
        
        setProcessingDocuments(prev => prev.map(doc => {
          if (doc.id === documentId) {
            const updatedStages = doc.stages.map((s, index) => ({
              ...s,
              completed: index < currentStage,
              current: index === currentStage
            }));
            
            return {
              ...doc,
              stages: updatedStages,
              progress: Math.round((currentStage + 1) / stages.length * 100)
            };
          }
          return doc;
        }));

        currentStage++;
        progress = Math.round(currentStage / stages.length * 100);
        
        setTimeout(processStage, stage.duration);
      } else {
        // Move to completed
        setProcessingDocuments(prev => {
          const completedDoc = prev.find(doc => doc.id === documentId);
          if (completedDoc) {
            setCompletedDocuments(prevCompleted => [...prevCompleted, {
              ...completedDoc,
              status: 'completed',
              progress: 100,
              stages: completedDoc.stages.map(stage => ({ ...stage, completed: true, current: false }))
            }]);
            return prev.filter(doc => doc.id !== documentId);
          }
          return prev;
        });
      }
    };

    processStage();
  };

  const ProcessingPipelineCard = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          NVIDIA NeMo Processing Pipeline
        </Typography>
        <List dense>
          {[
            { name: '1. Document Preprocessing', description: 'NeMo Retriever Extraction', color: 'primary' },
            { name: '2. Intelligent OCR', description: 'NeMoRetriever-OCR-v1 + Nemotron Parse', color: 'primary' },
            { name: '3. Small LLM Processing', description: 'Llama Nemotron Nano VL 8B', color: 'primary' },
            { name: '4. Embedding & Indexing', description: 'nv-embedqa-e5-v5', color: 'primary' },
            { name: '5. Large LLM Judge', description: 'Llama 3.1 Nemotron 70B', color: 'primary' },
            { name: '6. Intelligent Routing', description: 'Quality-based routing', color: 'primary' },
          ].map((stage, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                <Chip label={stage.name.split('.')[0]} color={stage.color as any} size="small" />
              </ListItemIcon>
              <ListItemText 
                primary={stage.name}
                secondary={stage.description}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );

  const DocumentUploadCard = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Upload Documents
        </Typography>
        <Box
          sx={{
            border: '2px dashed #ccc',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            cursor: 'pointer',
            '&:hover': {
              borderColor: 'primary.main',
              backgroundColor: 'action.hover',
            },
          }}
          onClick={() => {
            // Create a mock file input
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf,.png,.jpg,.jpeg,.tiff,.bmp';
            input.onchange = (e) => {
              const file = (e.target as HTMLInputElement).files?.[0];
              if (file) {
                handleDocumentUpload(file);
              }
            };
            input.click();
          }}
        >
          <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Click to Upload Document
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Maximum file size: 50MB
          </Typography>
        </Box>
        
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            Documents are processed through NVIDIA's NeMo models for intelligent extraction, 
            validation, and routing. Processing typically takes 30-60 seconds.
          </Typography>
        </Alert>
      </CardContent>
    </Card>
  );

  const ProcessingStatusCard = ({ document }: { document: DocumentItem }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{document.filename}</Typography>
          <Chip 
            label={document.status} 
            color={document.status === 'completed' ? 'success' : 'primary'} 
            size="small" 
          />
        </Box>
        
        <LinearProgress 
          variant="determinate" 
          value={document.progress} 
          sx={{ mb: 2 }} 
        />
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {document.progress}% Complete
        </Typography>
        
        <List dense>
          {document.stages.map((stage, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                {stage.completed ? (
                  <CheckCircle color="success" />
                ) : stage.current ? (
                  <LinearProgress sx={{ width: 20, height: 20 }} />
                ) : (
                  <div style={{ width: 20, height: 20, borderRadius: '50%', backgroundColor: '#e0e0e0' }} />
                )}
              </ListItemIcon>
              <ListItemText 
                primary={stage.name}
                secondary={stage.description}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );

  const CompletedDocumentCard = ({ document }: { document: DocumentItem }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{document.filename}</Typography>
          <Box>
            <Chip label="Completed" color="success" size="small" sx={{ mr: 1 }} />
            <Chip label="Auto-Approved" color="success" size="small" />
          </Box>
        </Box>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Quality Score: 4.2/5.0 | Processing Time: 45s
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" startIcon={<ViewIcon />}>
            View Results
          </Button>
          <Button size="small" startIcon={<DownloadIcon />}>
            Download
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Document Extraction & Processing
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload warehouse documents for intelligent extraction and processing using NVIDIA NeMo models
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="document processing tabs">
          <Tab label="Upload Documents" icon={<UploadIcon />} />
          <Tab label="Processing Status" icon={<SearchIcon />} />
          <Tab label="Completed Documents" icon={<ApprovedIcon />} />
          <Tab label="Analytics" icon={<AnalyticsIcon />} />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <DocumentUploadCard />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <ProcessingPipelineCard />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Grid container spacing={3}>
          {processingDocuments.length === 0 ? (
            <Grid item xs={12}>
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                  No documents currently processing
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Upload a document to see processing status
                </Typography>
              </Paper>
            </Grid>
          ) : (
            processingDocuments.map((doc) => (
              <Grid item xs={12} md={6} key={doc.id}>
                <ProcessingStatusCard document={doc} />
              </Grid>
            ))
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Grid container spacing={3}>
          {completedDocuments.length === 0 ? (
            <Grid item xs={12}>
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                  No completed documents
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Processed documents will appear here
                </Typography>
              </Paper>
            </Grid>
          ) : (
            completedDocuments.map((doc) => (
              <Grid item xs={12} md={6} key={doc.id}>
                <CompletedDocumentCard document={doc} />
              </Grid>
            ))
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Processing Statistics
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText primary="Total Documents" secondary="1,250" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Processed Today" secondary="45" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Average Quality" secondary="4.2/5.0" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Auto-Approved" secondary="78%" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quality Score Trends
                </Typography>
                <Box sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Quality trend chart would be displayed here
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
};

export default DocumentExtraction;
