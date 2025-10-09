"""
Document Processing API Router
Provides endpoints for document upload, processing, status, and results
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
import os
import asyncio

from chain_server.agents.document.models.document_models import (
    DocumentUploadResponse, DocumentProcessingResponse, DocumentResultsResponse,
    DocumentSearchRequest, DocumentSearchResponse, DocumentValidationRequest,
    DocumentValidationResponse, DocumentProcessingError
)
from chain_server.agents.document.mcp_document_agent import get_mcp_document_agent
from chain_server.agents.document.action_tools import DocumentActionTools

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/document", tags=["document"])

# Global document tools instance
_document_tools: Optional[DocumentActionTools] = None

async def get_document_tools() -> DocumentActionTools:
    """Get or create document action tools instance."""
    global _document_tools
    
    if _document_tools is None:
        _document_tools = DocumentActionTools()
        await _document_tools.initialize()
    
    return _document_tools

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    user_id: str = Form(default="anonymous"),
    metadata: Optional[str] = Form(default=None),
    tools: DocumentActionTools = Depends(get_document_tools)
):
    """
    Upload a document for processing through the NVIDIA NeMo pipeline.
    
    Args:
        file: Document file to upload (PDF, PNG, JPG, JPEG, TIFF, BMP)
        document_type: Type of document (invoice, receipt, BOL, etc.)
        user_id: User ID uploading the document
        metadata: Additional metadata as JSON string
        tools: Document action tools dependency
        
    Returns:
        DocumentUploadResponse with document ID and processing status
    """
    try:
        logger.info(f"Document upload request: {file.filename}, type: {document_type}")
        
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Create temporary file path
        document_id = str(uuid.uuid4())
        temp_dir = "/tmp/document_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"{document_id}_{file.filename}")
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse metadata
        parsed_metadata = {}
        if metadata:
            try:
                import json
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                logger.warning(f"Invalid metadata JSON: {metadata}")
        
        # Start document processing
        result = await tools.upload_document(
            file_path=temp_file_path,
            document_type=document_type,
            user_id=user_id,
            metadata=parsed_metadata
        )
        
        if result["success"]:
            # Schedule background processing
            background_tasks.add_task(
                process_document_background,
                document_id,
                temp_file_path,
                document_type,
                user_id,
                parsed_metadata
            )
            
            return DocumentUploadResponse(
                document_id=document_id,
                status="uploaded",
                message="Document uploaded successfully and processing started",
                estimated_processing_time=60
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/status/{document_id}", response_model=DocumentProcessingResponse)
async def get_document_status(
    document_id: str,
    tools: DocumentActionTools = Depends(get_document_tools)
):
    """
    Get the processing status of a document.
    
    Args:
        document_id: Document ID to check status for
        tools: Document action tools dependency
        
    Returns:
        DocumentProcessingResponse with current status and progress
    """
    try:
        logger.info(f"Getting status for document: {document_id}")
        
        result = await tools.get_document_status(document_id)
        
        if result["success"]:
            return DocumentProcessingResponse(
                document_id=document_id,
                status=result["status"],
                progress=result["progress"],
                current_stage=result["current_stage"],
                stages=[
                    {
                        "stage_name": stage["name"].lower().replace(" ", "_"),
                        "status": stage["status"],
                        "started_at": stage.get("started_at"),
                        "completed_at": stage.get("completed_at"),
                        "processing_time_ms": stage.get("processing_time_ms"),
                        "error_message": stage.get("error_message"),
                        "metadata": stage.get("metadata", {})
                    }
                    for stage in result["stages"]
                ],
                estimated_completion=datetime.fromtimestamp(result.get("estimated_completion", 0)) if result.get("estimated_completion") else None
            )
        else:
            raise HTTPException(status_code=404, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/results/{document_id}", response_model=DocumentResultsResponse)
async def get_document_results(
    document_id: str,
    tools: DocumentActionTools = Depends(get_document_tools)
):
    """
    Get the extraction results for a processed document.
    
    Args:
        document_id: Document ID to get results for
        tools: Document action tools dependency
        
    Returns:
        DocumentResultsResponse with extraction results and quality scores
    """
    try:
        logger.info(f"Getting results for document: {document_id}")
        
        result = await tools.extract_document_data(document_id)
        
        if result["success"]:
            return DocumentResultsResponse(
                document_id=document_id,
                filename=f"document_{document_id}.pdf",  # Mock filename
                document_type="invoice",  # Mock type
                extraction_results=result["extracted_data"],
                quality_score=result.get("quality_score"),
                routing_decision=result.get("routing_decision"),
                search_metadata=None,
                processing_summary={
                    "total_processing_time": result.get("processing_time_ms", 0),
                    "stages_completed": result.get("stages", []),
                    "confidence_scores": result.get("confidence_scores", {})
                }
            )
        else:
            raise HTTPException(status_code=404, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document results: {e}")
        raise HTTPException(status_code=500, detail=f"Results retrieval failed: {str(e)}")

@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    tools: DocumentActionTools = Depends(get_document_tools)
):
    """
    Search processed documents by content or metadata.
    
    Args:
        request: Search request with query and filters
        tools: Document action tools dependency
        
    Returns:
        DocumentSearchResponse with matching documents
    """
    try:
        logger.info(f"Searching documents with query: {request.query}")
        
        result = await tools.search_documents(
            search_query=request.query,
            filters=request.filters or {}
        )
        
        if result["success"]:
            return DocumentSearchResponse(
                results=result["results"],
                total_count=result["total_count"],
                query=request.query,
                search_time_ms=result["search_time_ms"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/validate/{document_id}", response_model=DocumentValidationResponse)
async def validate_document(
    document_id: str,
    request: DocumentValidationRequest,
    tools: DocumentActionTools = Depends(get_document_tools)
):
    """
    Validate document extraction quality and accuracy.
    
    Args:
        document_id: Document ID to validate
        request: Validation request with type and rules
        tools: Document action tools dependency
        
    Returns:
        DocumentValidationResponse with validation results
    """
    try:
        logger.info(f"Validating document: {document_id}")
        
        result = await tools.validate_document_quality(
            document_id=document_id,
            validation_type=request.validation_type
        )
        
        if result["success"]:
            return DocumentValidationResponse(
                document_id=document_id,
                validation_status="completed",
                quality_score=result["quality_score"],
                validation_notes=request.validation_rules.get("notes") if request.validation_rules else None,
                validated_by=request.reviewer_id or "system",
                validation_timestamp=datetime.now()
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.get("/analytics")
async def get_document_analytics(
    time_range: str = "week",
    metrics: Optional[List[str]] = None,
    tools: DocumentActionTools = Depends(get_document_tools)
):
    """
    Get analytics and metrics for document processing.
    
    Args:
        time_range: Time range for analytics (today, week, month)
        metrics: Specific metrics to retrieve
        tools: Document action tools dependency
        
    Returns:
        Analytics data with metrics and trends
    """
    try:
        logger.info(f"Getting document analytics for time range: {time_range}")
        
        result = await tools.get_document_analytics(
            time_range=time_range,
            metrics=metrics or []
        )
        
        if result["success"]:
            return {
                "time_range": time_range,
                "metrics": result["metrics"],
                "trends": result["trends"],
                "summary": result["summary"],
                "generated_at": datetime.now()
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@router.post("/approve/{document_id}")
async def approve_document(
    document_id: str,
    approver_id: str = Form(...),
    approval_notes: Optional[str] = Form(default=None),
    tools: DocumentActionTools = Depends(get_document_tools)
):
    """
    Approve document for WMS integration.
    
    Args:
        document_id: Document ID to approve
        approver_id: User ID of approver
        approval_notes: Approval notes
        tools: Document action tools dependency
        
    Returns:
        Approval confirmation
    """
    try:
        logger.info(f"Approving document: {document_id}")
        
        result = await tools.approve_document(
            document_id=document_id,
            approver_id=approver_id,
            approval_notes=approval_notes
        )
        
        if result["success"]:
            return {
                "document_id": document_id,
                "approval_status": "approved",
                "approver_id": approver_id,
                "approval_timestamp": datetime.now(),
                "approval_notes": approval_notes
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document approval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")

@router.post("/reject/{document_id}")
async def reject_document(
    document_id: str,
    rejector_id: str = Form(...),
    rejection_reason: str = Form(...),
    suggestions: Optional[str] = Form(default=None),
    tools: DocumentActionTools = Depends(get_document_tools)
):
    """
    Reject document and provide feedback.
    
    Args:
        document_id: Document ID to reject
        rejector_id: User ID of rejector
        rejection_reason: Reason for rejection
        suggestions: Suggestions for improvement
        tools: Document action tools dependency
        
    Returns:
        Rejection confirmation
    """
    try:
        logger.info(f"Rejecting document: {document_id}")
        
        suggestions_list = []
        if suggestions:
            try:
                import json
                suggestions_list = json.loads(suggestions)
            except json.JSONDecodeError:
                suggestions_list = [suggestions]
        
        result = await tools.reject_document(
            document_id=document_id,
            rejector_id=rejector_id,
            rejection_reason=rejection_reason,
            suggestions=suggestions_list
        )
        
        if result["success"]:
            return {
                "document_id": document_id,
                "rejection_status": "rejected",
                "rejector_id": rejector_id,
                "rejection_reason": rejection_reason,
                "suggestions": suggestions_list,
                "rejection_timestamp": datetime.now()
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document rejection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rejection failed: {str(e)}")

async def process_document_background(
    document_id: str,
    file_path: str,
    document_type: str,
    user_id: str,
    metadata: Dict[str, Any]
):
    """Background task for document processing."""
    try:
        logger.info(f"Starting background processing for document: {document_id}")
        
        # Simulate processing stages
        stages = [
            "preprocessing",
            "ocr_extraction", 
            "llm_processing",
            "validation",
            "routing"
        ]
        
        for i, stage in enumerate(stages):
            logger.info(f"Processing stage {i+1}/{len(stages)}: {stage}")
            await asyncio.sleep(2)  # Simulate processing time
        
        logger.info(f"Background processing completed for document: {document_id}")
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except OSError:
            logger.warning(f"Could not remove temporary file: {file_path}")
            
    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}")

@router.get("/health")
async def document_health_check():
    """Health check endpoint for document processing service."""
    return {
        "status": "healthy",
        "service": "document_processing",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }
