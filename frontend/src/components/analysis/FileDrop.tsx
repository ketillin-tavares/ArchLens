import {
  useRef,
  useState,
  type DragEvent,
  type MouseEvent as ReactMouseEvent,
} from "react";
import { TOKENS } from "@/config/tokens";
import { FileIcon } from "./FileIcon";

export const UPLOAD_ACCEPT_ATTR =
  ".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf";

interface FileDropProps {
  file: File | null;
  error?: string;
  onFile: (file: File | null) => void;
}

export function FileDrop({ file, error, onFile }: FileDropProps): JSX.Element {
  const [over, setOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleClear = (event: ReactMouseEvent<HTMLButtonElement>): void => {
    event.stopPropagation();
    onFile(null);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    setOver(false);
    const dropped = event.dataTransfer.files[0];
    if (dropped) {
      onFile(dropped);
    }
  };

  return (
    <>
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `1.5px dashed ${
            error ? TOKENS.bad : over ? TOKENS.blue : TOKENS.line
          }`,
          background: error
            ? "#FEF2F2"
            : over
              ? TOKENS.blueSoft
              : TOKENS.mist,
          borderRadius: 10,
          padding: file ? "20px 20px" : "40px 24px",
          textAlign: "center",
          cursor: "pointer",
          transition: "all 100ms ease",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={UPLOAD_ACCEPT_ATTR}
          hidden
          onChange={(event) => onFile(event.target.files?.[0] ?? null)}
        />
        {file ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              textAlign: "left",
            }}
          >
            <FileIcon ext={file.name.split(".").pop()?.toLowerCase() ?? ""} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontFamily: "Geist",
                  fontSize: 14,
                  fontWeight: 500,
                  color: TOKENS.ink,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {file.name}
              </div>
              <div
                style={{
                  fontFamily: "Geist Mono",
                  fontSize: 11,
                  color: TOKENS.slate,
                  marginTop: 2,
                }}
              >
                {(file.size / 1024 / 1024).toFixed(2)} MB · pronto para envio
              </div>
            </div>
            <button
              onClick={handleClear}
              style={{
                background: "transparent",
                border: `1px solid ${TOKENS.line}`,
                borderRadius: 6,
                padding: "6px 10px",
                fontFamily: "Geist Mono",
                fontSize: 11,
                color: TOKENS.slate,
                cursor: "pointer",
              }}
            >
              remover
            </button>
          </div>
        ) : (
          <>
            <svg
              width="28"
              height="28"
              viewBox="0 0 20 20"
              fill="none"
              stroke={TOKENS.slate}
              strokeWidth="1.5"
              style={{ marginBottom: 10 }}
            >
              <path d="M10 3v10m0-10l-4 4m4-4l4 4M4 15v2h12v-2" />
            </svg>
            <div
              style={{
                fontFamily: "Geist",
                fontSize: 14,
                fontWeight: 500,
                color: TOKENS.ink,
                marginBottom: 4,
              }}
            >
              Arraste um arquivo ou clique para selecionar
            </div>
            <div
              style={{
                fontFamily: "Geist Mono",
                fontSize: 11,
                color: TOKENS.slate,
              }}
            >
              PNG · JPG · JPEG · PDF · até 10 MB
            </div>
          </>
        )}
      </div>
      {error && (
        <div
          style={{
            marginTop: 8,
            fontFamily: "Geist",
            fontSize: 12,
            color: TOKENS.bad,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="6" cy="6" r="5" />
            <path d="M6 3.5V6m0 2v.1" />
          </svg>
          {error}
        </div>
      )}
    </>
  );
}
