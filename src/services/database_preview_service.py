"""Database Preview and Dynamic SQL Export Service.

Provides safe, read-only live schema introspection and clean DDL generation
using SQLAlchemy inspection facilities without hardcoding or mutations.
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy import Engine, inspect
from sqlalchemy.orm import Session

from src.contracts.settings.database_preview_models import (
    ColumnMetadataDTO,
    DatabaseOverviewDTO,
    DatabasePreviewResponseDTO,
    ForeignKeyDetailDTO,
    SqlExportResponseDTO,
    TableMetadataDTO,
)
from src.database.engine import get_database_engine
from src.logging import get_logger

logger = get_logger("src.services.database_preview_service", component="settings")


class DatabasePreviewService:
    """Read-only schema introspection and DDL generation service."""

    @classmethod
    def get_database_preview(
        cls,
        db: Optional[Session] = None,
        engine: Optional[Engine] = None,
    ) -> DatabasePreviewResponseDTO:
        """Introspect connected database to extract tables, columns, primary keys, and foreign keys."""
        target_engine = engine or (db.get_bind() if db else get_database_engine())
        inspector = inspect(target_engine)

        dialect_name = target_engine.dialect.name
        raw_db = target_engine.url.database or ("acc_rmc_prod" if dialect_name == "postgresql" else "acc_rmc_dev")
        db_name = os.path.basename(raw_db) if ("/" in raw_db or "\\" in raw_db) else raw_db
        now_str = datetime.now(timezone.utc).isoformat()

        # Get base tables
        schema_name = "public" if dialect_name == "postgresql" else None
        table_names = sorted(inspector.get_table_names(schema=schema_name))

        total_cols = 0
        total_fks = 0
        tables_list: List[TableMetadataDTO] = []

        for tbl_name in table_names:
            raw_columns = inspector.get_columns(tbl_name, schema=schema_name)
            raw_pks = inspector.get_pk_constraint(tbl_name, schema=schema_name)
            raw_fks = inspector.get_foreign_keys(tbl_name, schema=schema_name)

            pk_cols = set(raw_pks.get("constrained_columns", []) if raw_pks else [])

            # Map FKs by constrained column name for rapid lookup
            fk_map: Dict[str, ForeignKeyDetailDTO] = {}
            parsed_fks: List[ForeignKeyDetailDTO] = []
            for fk in raw_fks:
                c_cols = fk.get("constrained_columns", [])
                r_cols = fk.get("referred_columns", [])
                r_table = fk.get("referred_table", "")
                r_schema = fk.get("referred_schema") or "public"
                c_name = fk.get("name")

                for idx, col_name in enumerate(c_cols):
                    ref_col = r_cols[idx] if idx < len(r_cols) else (r_cols[0] if r_cols else "id")
                    fk_dto = ForeignKeyDetailDTO(
                        constraint_name=c_name,
                        constrained_column=col_name,
                        referred_schema=r_schema,
                        referred_table=r_table,
                        referred_column=ref_col,
                    )
                    fk_map[col_name] = fk_dto
                    parsed_fks.append(fk_dto)

            parsed_columns: List[ColumnMetadataDTO] = []
            for col in raw_columns:
                c_name = col.get("name", "")
                c_type_raw = str(col.get("type", "TEXT"))
                c_type_fmt = cls._format_column_type(c_type_raw)
                c_null = bool(col.get("nullable", True))
                c_is_pk = c_name in pk_cols
                c_default = str(col.get("default")) if col.get("default") is not None else None
                c_fk = fk_map.get(c_name)

                parsed_columns.append(
                    ColumnMetadataDTO(
                        name=c_name,
                        type=c_type_fmt,
                        nullable=c_null,
                        primary_key=c_is_pk,
                        default_value=c_default,
                        foreign_key=c_fk,
                    )
                )

            total_cols += len(parsed_columns)
            total_fks += len(parsed_fks)

            tables_list.append(
                TableMetadataDTO(
                    name=tbl_name,
                    schema_name=schema_name or "public",
                    column_count=len(parsed_columns),
                    primary_keys=list(pk_cols),
                    foreign_keys=parsed_fks,
                    foreign_relations_count=len(parsed_fks),
                    columns=parsed_columns,
                )
            )

        overview = DatabaseOverviewDTO(
            database_name=db_name,
            dialect=dialect_name,
            public_tables_count=len(tables_list),
            total_columns_count=total_cols,
            foreign_keys_count=total_fks,
            retrieved_at_utc=now_str,
        )

        return DatabasePreviewResponseDTO(
            overview=overview,
            tables=tables_list,
        )

    @classmethod
    def generate_sql_ddl_export(
        cls,
        db: Optional[Session] = None,
        engine: Optional[Engine] = None,
    ) -> SqlExportResponseDTO:
        """Generate clean, valid PostgreSQL DDL export statements for all public tables."""
        preview = cls.get_database_preview(db=db, engine=engine)
        overview = preview.overview
        tables = preview.tables

        now_utc = datetime.now(timezone.utc)
        timestamp_str = now_utc.strftime("%Y%m%d_%H%M%S")
        clean_db_name = overview.database_name.replace(".sqlite3", "").replace(".db", "")
        filename = f"{clean_db_name}_schema_{timestamp_str}.sql"

        ddl_lines: List[str] = [
            "-- =========================================================================",
            f"-- ACC Ready-Mix Concrete Platform Database Schema Export",
            f"-- Database: {overview.database_name}",
            f"-- Dialect: {overview.dialect.upper()}",
            f"-- Tables: {overview.public_tables_count} | Foreign Keys: {overview.foreign_keys_count} | Total Columns: {overview.total_columns_count}",
            f"-- Generated At (UTC): {now_utc.isoformat()}",
            "-- =========================================================================",
            "",
            "SET statement_timeout = 0;",
            "SET client_encoding = 'UTF8';",
            "SET standard_conforming_strings = on;",
            "",
        ]

        for table in tables:
            ddl_lines.append(f"CREATE TABLE IF NOT EXISTS public.{table.name} (")
            col_definitions: List[str] = []

            for col in table.columns:
                null_clause = "" if col.nullable else " NOT NULL"
                default_clause = f" DEFAULT {col.default_value}" if col.default_value else ""
                col_definitions.append(f"    {col.name} {col.type}{default_clause}{null_clause}")

            # Primary Key constraint
            if table.primary_keys:
                pk_str = ", ".join(table.primary_keys)
                col_definitions.append(f"    CONSTRAINT pk_{table.name} PRIMARY KEY ({pk_str})")

            # Foreign Key constraints
            for idx, fk in enumerate(table.foreign_keys):
                c_name = fk.constraint_name or f"fk_{table.name}_{fk.constrained_column}"
                col_definitions.append(
                    f"    CONSTRAINT {c_name} FOREIGN KEY ({fk.constrained_column}) REFERENCES public.{fk.referred_table} ({fk.referred_column})"
                )

            ddl_lines.append(",\n".join(col_definitions))
            ddl_lines.append(");")
            ddl_lines.append("")

        sql_ddl = "\n".join(ddl_lines)

        return SqlExportResponseDTO(
            database_name=overview.database_name,
            dialect=overview.dialect,
            tables_count=overview.public_tables_count,
            foreign_keys_count=overview.foreign_keys_count,
            generated_at_utc=now_utc.isoformat(),
            sql_ddl=sql_ddl,
            filename=filename,
        )

    @staticmethod
    def _format_column_type(raw_type: str) -> str:
        """Format raw SQLAlchemy column type into standard, readable SQL type string."""
        raw_upper = raw_type.upper()
        if "VARCHAR" in raw_upper or "CHARACTER VARYING" in raw_upper:
            if "(" in raw_upper:
                return raw_upper
            return "Character Varying"
        if "UUID" in raw_upper:
            return "Uuid"
        if "BOOLEAN" in raw_upper or "BOOL" in raw_upper:
            return "Boolean"
        if "INTEGER" in raw_upper or "INT" in raw_upper:
            if "BIGINT" in raw_upper:
                return "Bigint"
            if "SMALLINT" in raw_upper:
                return "Smallint"
            return "Integer"
        if "FLOAT" in raw_upper or "DOUBLE" in raw_upper or "REAL" in raw_upper:
            return "Double Precision"
        if "NUMERIC" in raw_upper or "DECIMAL" in raw_upper:
            return raw_upper if "(" in raw_upper else "Numeric"
        if "TIMESTAMP" in raw_upper:
            if "WITH TIME ZONE" in raw_upper or "TZ" in raw_upper:
                return "Timestamp With Time Zone"
            return "Timestamp Without Time Zone"
        if "JSON" in raw_upper or "JSONB" in raw_upper:
            return "Jsonb" if "JSONB" in raw_upper else "Json"
        if "TEXT" in raw_upper:
            return "Text"
        if "DATE" in raw_upper:
            return "Date"
        if "BYTEA" in raw_upper or "BLOB" in raw_upper:
            return "Bytea"
        return raw_type.title()
