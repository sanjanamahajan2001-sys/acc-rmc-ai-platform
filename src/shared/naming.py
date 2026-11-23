"""Domain Naming Conventions and Standard Enforcers.

This module provides helper utilities to validate naming compliance across
modules, API routes, database tables, and canonical entities according to the
ACC RMC AI Platform frozen engineering standards.
"""

import re

# Naming Pattern Regular Expressions
SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
PASCAL_CASE_PATTERN = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
UPPER_SNAKE_CASE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
KEBAB_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9\-]*$")
DB_TABLE_PATTERN = re.compile(r"^tbl_[a-z][a-z0-9_]*$")


def is_snake_case(name: str) -> bool:
    """Check if a string strictly follows snake_case naming convention."""
    return bool(SNAKE_CASE_PATTERN.match(name))


def is_pascal_case(name: str) -> bool:
    """Check if a string strictly follows PascalCase naming convention."""
    return bool(PASCAL_CASE_PATTERN.match(name))


def is_upper_snake_case(name: str) -> bool:
    """Check if a string strictly follows UPPER_SNAKE_CASE naming convention."""
    return bool(UPPER_SNAKE_CASE_PATTERN.match(name))


def is_kebab_case(name: str) -> bool:
    """Check if a string strictly follows kebab-case naming convention."""
    return bool(KEBAB_CASE_PATTERN.match(name))


def is_valid_db_table_name(table_name: str) -> bool:
    """Check if a database table name complies with tbl_ prefix and snake_case."""
    return bool(DB_TABLE_PATTERN.match(table_name))
