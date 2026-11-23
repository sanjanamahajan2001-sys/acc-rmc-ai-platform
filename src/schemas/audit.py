"""Audit & Governance Canonical DTO Schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ActorInfoDTO(BaseModel):
    user_id: Optional[str] = None
    username: str = "SYSTEM"
    email: Optional[str] = None
    full_name: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class TargetInfoDTO(BaseModel):
    entity_type: str = "SYSTEM"
    entity_id: str = "GLOBAL"
    entity_name: Optional[str] = None


class AuditEventItemDTO(BaseModel):
    id: str
    timestamp: datetime
    module: str
    event_type: str
    action: str
    severity: str
    result: str
    actor: ActorInfoDTO
    target: TargetInfoDTO
    correlation_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditEventListResponseDTO(BaseModel):
    items: List[AuditEventItemDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditMetricsDTO(BaseModel):
    total_events: int
    successful_events: int
    failed_events: int
    denied_events: int
    events_last_24h: int
    module_breakdown: Dict[str, int]


class AuditCorrelationResponseDTO(BaseModel):
    correlation_id: str
    total_events: int
    events: List[AuditEventItemDTO]
