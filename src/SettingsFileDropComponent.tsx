"use client";

import React, { useState } from "react";
import { useDropzone } from "react-dropzone";

type Props = {
  /** Optional: get notified when a file is dropped */
  onFileSelected?: (file: File) => void;
};

const SettingsFileDropComponent: React.FC<Props> = ({ onFileSelected }) => {
  const [file, setFile] = useState<File | null>(null);
  const [parsed, setParsed] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    accept: { "application/json": [".json"] },
    multiple: false,
    noClick: true, // we’ll handle clicks manually
    onDrop: async (acceptedFiles) => {
      setError(null);
      setParsed(null);
      setFile(null);

      if (!acceptedFiles?.length) return;
      const f = acceptedFiles[0];
      setFile(f);
      onFileSelected?.(f);

      try {
        const text = await f.text();
        const data = JSON.parse(text);
        setParsed(data);
      } catch (err) {
        console.error(err);
        setError("Couldn't parse JSON. Please check the file contents.");
      }
    },
  });

  const handleClear = () => {
    setFile(null);
    setParsed(null);
    setError(null);
  };

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer select-none ${
          isDragActive ? "opacity-80" : ""
        }`}
        onClick={open}
      >
        <input {...getInputProps()} />
        <p className="font-medium">
          {isDragActive
            ? "Drop the stitch settings JSON here…"
            : "Drop a stitch settings JSON here, or click to select"}
        </p>
        <p className="text-sm opacity-70 mt-1">Accepted: .json</p>
      </div>

      {file && (
        <div className="text-sm flex items-center justify-between">
          <p>
            <strong>Selected:</strong> {file.name}{" "}
            <span className="opacity-70">
              ({(file.size / 1024).toFixed(1)} KB)
            </span>
          </p>
          <button
            type="button"
            onClick={handleClear}
            className="px-2 py-1 rounded border"
          >
            Clear
          </button>
        </div>
      )}

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {parsed && (
        <pre
          className="text-xs rounded-md"
          style={{
            maxHeight: 240,
            overflow: "auto",
            background: "#0f172a",
            color: "#e2e8f0",
            padding: 12,
          }}
        >
          {JSON.stringify(parsed, null, 2)}
        </pre>
      )}
    </div>
  );
};

export default SettingsFileDropComponent;
