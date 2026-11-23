"""Contract Data Transfer Objects for Database Preview & SQL Export Settings."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ForeignKeyDetailDTO(BaseModel):
    """Foreign key relationship metadata for a column."""
    constraint_name: Optional[str] = None
    constrained_column: str
    referred_schema: Optional[str] = "public"
    referred_table: str
    referred_column: str


class ColumnMetadataDTO(BaseModel):
    """Schema metadata for a single database table column."""
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    default_value: Optional[str] = None
    foreign_key: Optional[ForeignKeyDetailDTO] = None


class TableMetadataDTO(BaseModel):
    """Schema metadata for a single database table."""
    name: str
    schema_name: str = "public"
    column_count: int = 0
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[ForeignKeyDetailDTO] = Field(default_factory=list)
    foreign_relations_count: int = 0
    columns: List[ColumnMetadataDTO] = Field(default_factory=list)


class DatabaseOverviewDTO(BaseModel):
    """High-level database statistical overview."""
    database_name: str
    dialect: str = "postgresql"
    public_tables_count: int = 0
    total_columns_count: int = 0
    foreign_keys_count: int = 0
    retrieved_at_utc: str


class DatabasePreviewResponseDTO(BaseModel):
    """Complete response payload for live database introspection."""
    overview: DatabaseOverviewDTO
    tables: List[TableMetadataDTO] = Field(default_factory=list)


class SqlExportResponseDTO(BaseModel):
    """Response payload for generated SQL schema DDL export."""
    database_name: str
    dialect: str = "postgresql"
    tables_count: int = 0
    foreign_keys_count: int = 0
    generated_at_utc: str
    sql_ddl: str
    filename: str
