export interface ConnectorFileInfo {
  file_id: string;
  file_name: string;
  file_size?: number;
  upload_date?: string;
  metadata?: Record<string, unknown>;
}

export interface ConnectorFilesResponse {
  files: ConnectorFileInfo[];
}

export interface FileUploadResponse {
  file_paths: string[];
  file_names: string[];
  zip_metadata_file_id: string | null;
}

export async function updateConnectorFiles(
  connectorId: number,
  fileIdsToRemove: string[],
  filesToAdd: File[]
): Promise<void> {
  const formData = new FormData();

  // Add files to remove as JSON
  formData.append("file_ids_to_remove", JSON.stringify(fileIdsToRemove));

  // Add new files
  filesToAdd.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(
    `/api/manage/admin/connector/${connectorId}/files/update`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(
      `Failed to update connector files (${response.status}): ${
        error.detail || "Unknown error"
      }`
    );
  }
}

export async function updateFileMetadata(
  connectorId: number,
  fileMetadata: Record<string, Record<string, unknown>>
): Promise<void> {
  const response = await fetch(
    `/api/manage/admin/connector/${connectorId}/files/metadata`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_metadata: fileMetadata }),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(
      `Failed to update file metadata (${response.status}): ${
        error.detail || "Unknown error"
      }`
    );
  }
}
