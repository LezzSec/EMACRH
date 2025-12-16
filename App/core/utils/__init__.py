# -*- coding: utf-8 -*-
"""Package utilitaire pour EMAC."""

from .app_paths import (
    get_base_dir,
    get_data_dir,
    get_logs_dir,
    get_documents_dir,
    get_log_file_path,
    get_document_path,
    is_frozen,
)

__all__ = [
    'get_base_dir',
    'get_data_dir',
    'get_logs_dir',
    'get_documents_dir',
    'get_log_file_path',
    'get_document_path',
    'is_frozen',
]
