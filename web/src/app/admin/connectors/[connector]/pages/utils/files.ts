import { toast } from "@/hooks/useToast";
import { createConnector, runConnector } from "@/lib/connector";
import { createCredential, linkCredential } from "@/lib/credential";
import { FileConfig } from "@/lib/connectors/connectors";
import { AccessType, ValidSources } from "@/lib/types";
import type { FileMetadata } from "@/components/admin/connectors/FileMetadataEditor";

export const submitFiles = async (
  selectedFiles: File[],
  name: string,
  access_type: string,
  groups?: number[],
  kgProcessingEnabled?: boolean,
  kgCoverageDays?: number | null,
  fileMetadata?: Record<string, FileMetadata>
) => {
  const formData = new FormData();

  selectedFiles.forEach((file) => {
    formData.append("files", file);
  });

  // Attach per-file metadata if provided and non-empty
  if (fileMetadata && Object.keys(fileMetadata).length > 0) {
    // Filter out empty metadata objects
    const nonEmptyMetadata = Object.fromEntries(
      Object.entries(fileMetadata).filter(
        ([, meta]) => Object.keys(meta).length > 0
      )
    );
    if (Object.keys(nonEmptyMetadata).length > 0) {
      formData.append("metadata", JSON.stringify(nonEmptyMetadata));
    }
  }

  const response = await fetch("/api/manage/admin/connector/file/upload", {
    method: "POST",
    body: formData,
  });
  const responseJson = await response.json();
  if (!response.ok) {
    toast.error(`Unable to upload files - ${responseJson.detail}`);
    return;
  }

  const filePaths = responseJson.file_paths as string[];
  const fileNames = responseJson.file_names as string[];
  const zipMetadataFileId = responseJson.zip_metadata_file_id as string | null;

  const [connectorErrorMsg, connector] = await createConnector<FileConfig>({
    name: "FileConnector-" + Date.now(),
    source: ValidSources.File,
    input_type: "load_state",
    connector_specific_config: {
      file_locations: filePaths,
      file_names: fileNames,
      zip_metadata_file_id: zipMetadataFileId,
    },
    refresh_freq: null,
    prune_freq: null,
    indexing_start: null,
    access_type: access_type,
    groups: groups,
    kg_processing_enabled: kgProcessingEnabled ?? false,
    kg_coverage_days: kgCoverageDays ?? null,
  });
  if (connectorErrorMsg || !connector) {
    toast.error(`Unable to create connector - ${connectorErrorMsg}`);
    return;
  }

  // Since there is no "real" credential associated with a file connector
  // we create a dummy one here so that we can associate the CC Pair with a
  // user. This is needed since the user for a CC Pair is found via the credential
  // associated with it.
  const createCredentialResponse = await createCredential({
    credential_json: {},
    admin_public: true,
    source: ValidSources.File,
    curator_public: true,
    groups: groups,
    name,
  });
  if (!createCredentialResponse.ok) {
    const errorMsg = await createCredentialResponse.text();
    toast.error(`Error creating credential for CC Pair - ${errorMsg}`);
    return false;
  }
  const credentialId = (await createCredentialResponse.json()).id;

  const credentialResponse = await linkCredential(
    connector.id,
    credentialId,
    name,
    access_type as AccessType,
    groups
  );
  if (!credentialResponse.ok) {
    const credentialResponseJson = await credentialResponse.json();
    toast.error(
      `Unable to link connector to credential - ${credentialResponseJson.detail}`
    );
    return false;
  }

  const runConnectorErrorMsg = await runConnector(connector.id, [0]);
  if (runConnectorErrorMsg) {
    toast.error(`Unable to run connector - ${runConnectorErrorMsg}`);
    return false;
  }

  toast.success("Successfully uploaded files!");
  return true;
};
