import { apiClient, resolveBaseUrl, getAuthToken } from './apiClient';

export interface ForeignKeyDetailDTO {
  constraint_name?: string;
  constrained_column: string;
  referred_schema?: string;
  referred_table: string;
  referred_column: string;
}

export interface ColumnMetadataDTO {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default_value?: string;
  foreign_key?: ForeignKeyDetailDTO;
}

export interface TableMetadataDTO {
  name: string;
  schema_name: string;
  column_count: number;
  primary_keys: string[];
  foreign_keys: ForeignKeyDetailDTO[];
  foreign_relations_count: number;
  columns: ColumnMetadataDTO[];
}

export interface DatabaseOverviewDTO {
  database_name: string;
  dialect: string;
  public_tables_count: number;
  total_columns_count: number;
  foreign_keys_count: number;
  retrieved_at_utc: string;
}

export interface DatabasePreviewResponseDTO {
  overview: DatabaseOverviewDTO;
  tables: TableMetadataDTO[];
}

export interface SqlExportResponseDTO {
  database_name: string;
  dialect: string;
  tables_count: number;
  foreign_keys_count: number;
  generated_at_utc: string;
  sql_ddl: string;
  filename: string;
}

export interface DesignStandardOptionDTO {
  code: string;
  name: string;
  jurisdiction: string;
  formula: string;
  default_z: number;
  description: string;
}

export interface ExposureConstraintItemDTO {
  min_cement_kg_m3: number;
  max_wb_ratio: number;
  min_grade: string;
}

export interface ScmSubstitutionBoundDTO {
  min_percent: number;
  max_percent: number;
  default_percent: number;
}

export interface EngineeringCalibreSettingsDTO {
  id?: string;
  standard_code: string;
  standard_name: string;
  confidence_multiplier_z: number;
  target_strength_formula: string;
  air_volume_fraction: number;
  air_volume_percent: number;
  exposure_constraints_json: Record<string, ExposureConstraintItemDTO>;
  scm_substitution_bounds_json: Record<string, ScmSubstitutionBoundDTO>;
  specific_gravities_json?: Record<string, number>;
  is_active: boolean;
  updated_by_username?: string;
  updated_at?: string;
  available_standards: DesignStandardOptionDTO[];
}

export const fetchDatabasePreview = async (): Promise<DatabasePreviewResponseDTO> => {
  return await apiClient.get<DatabasePreviewResponseDTO>('/settings/database/preview');
};

export const fetchSqlExport = async (): Promise<SqlExportResponseDTO> => {
  return await apiClient.get<SqlExportResponseDTO>('/settings/database/export/sql');
};

export const fetchEngineeringSettings = async (): Promise<EngineeringCalibreSettingsDTO> => {
  return await apiClient.get<EngineeringCalibreSettingsDTO>('/settings/engineering-calibre');
};

export const updateEngineeringSettings = async (
  payload: EngineeringCalibreSettingsDTO
): Promise<EngineeringCalibreSettingsDTO> => {
  return await apiClient.put<EngineeringCalibreSettingsDTO>('/settings/engineering-calibre', payload);
};

export const resetEngineeringSettings = async (): Promise<EngineeringCalibreSettingsDTO> => {
  return await apiClient.post<EngineeringCalibreSettingsDTO>('/settings/engineering-calibre/reset', {});
};

export const downloadSqlExport = async (): Promise<void> => {
  const token = getAuthToken();
  const baseUrl = resolveBaseUrl();
  const response = await fetch(`${baseUrl}/settings/database/export/sql/download`, {
    method: 'GET',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    throw new Error(`SQL export download failed with status ${response.status}`);
  }

  const disposition = response.headers.get('content-disposition');
  let filename = 'acc_rmc_database_schema.sql';
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  const arrayBuffer = await response.arrayBuffer();
  const blob = new Blob([arrayBuffer], { type: 'application/sql' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    if (document.body.contains(a)) {
      document.body.removeChild(a);
    }
    window.URL.revokeObjectURL(url);
  }, 10000);
};
