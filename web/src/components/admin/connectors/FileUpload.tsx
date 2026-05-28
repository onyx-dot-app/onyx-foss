import { useFormikContext } from "formik";
import { FC, useState } from "react";
import React from "react";
import Dropzone from "react-dropzone";
import {
  FileMetadataEditor,
  type FileMetadata,
} from "@/components/admin/connectors/FileMetadataEditor";
import Text from "@/refresh-components/texts/Text";

interface FileUploadProps {
  selectedFiles: File[];
  setSelectedFiles: (files: File[]) => void;
  message?: string;
  name?: string;
  multiple?: boolean;
  accept?: string;
  onMetadataChange?: (metadata: Record<string, FileMetadata>) => void;
}

export const FileUpload: FC<FileUploadProps> = ({
  name,
  selectedFiles,
  setSelectedFiles,
  message,
  multiple = true,
  accept,
  onMetadataChange,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [expandedFile, setExpandedFile] = useState<string | null>(null);
  const [perFileMetadata, setPerFileMetadata] = useState<
    Record<string, FileMetadata>
  >({});
  const { setFieldValue } = useFormikContext();

  const handleMetadataChange = (
    fileName: string,
    metadata: FileMetadata
  ) => {
    const updated = { ...perFileMetadata, [fileName]: metadata };
    setPerFileMetadata(updated);
    onMetadataChange?.(updated);
    // Also store in Formik so parent forms can read it without prop threading
    setFieldValue("file_metadata", updated);
  };

  return (
    <div>
      <Dropzone
        onDrop={(acceptedFiles) => {
          let filesToSet: File[] = [];
          if (multiple) {
            filesToSet = acceptedFiles;
          } else {
            const acceptedFile = acceptedFiles[0];
            if (acceptedFile !== undefined) {
              filesToSet = [acceptedFile];
            }
          }

          if (filesToSet !== undefined) {
            setSelectedFiles(filesToSet);
          }

          setDragActive(false);
          if (name) {
            setFieldValue(name, multiple ? filesToSet : filesToSet[0]);
          }
        }}
        onDragLeave={() => setDragActive(false)}
        onDragEnter={() => setDragActive(true)}
        multiple={multiple}
        accept={accept ? { [accept]: [] } : undefined}
      >
        {({ getRootProps, getInputProps }) => (
          <section>
            <div
              {...getRootProps()}
              className={
                "flex flex-col items-center w-full px-4 py-12 rounded-sm " +
                "shadow-lg tracking-wide border border-border cursor-pointer" +
                (dragActive ? " border-accent" : "")
              }
            >
              <input {...getInputProps()} />
              <b className="text-text-darker">
                {message ||
                  `Drag and drop ${
                    multiple ? "some files" : "a file"
                  } here, or click to select ${multiple ? "files" : "a file"}`}
              </b>
            </div>
          </section>
        )}
      </Dropzone>

      {selectedFiles.length > 0 && (
        <div className="mt-4">
          <h2 className="text-sm font-bold">
            Selected File{multiple ? "s" : ""}
          </h2>
          <ul className="space-y-1 mt-1">
            {selectedFiles.map((file) => (
              <li key={file.name}>
                <div className="flex items-center gap-2">
                  <p className="text-sm mr-2">{file.name}</p>
                  <button
                    type="button"
                    className="text-xs text-accent hover:underline"
                    onClick={() =>
                      setExpandedFile(
                        expandedFile === file.name ? null : file.name
                      )
                    }
                  >
                    {expandedFile === file.name
                      ? "Hide metadata"
                      : "Add metadata"}
                  </button>
                </div>
                {expandedFile === file.name && (
                  <div className="mt-2 ml-4">
                    <Text as="p" figureSmallValue className="mb-2 text-text-500">
                      Optional metadata for {file.name}
                    </Text>
                    <FileMetadataEditor
                      fileName={file.name}
                      initialMetadata={perFileMetadata[file.name] ?? {}}
                      onChange={handleMetadataChange}
                    />
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

