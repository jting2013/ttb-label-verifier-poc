import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { FileImage, UploadCloud } from "lucide-react";

interface UploadPanelProps {
  busy: boolean;
  onUpload: (files: File[]) => Promise<void>;
}

export function UploadPanel({ busy, onUpload }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [queued, setQueued] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);

  function addFiles(fileList: FileList | null) {
    if (!fileList) return;
    const images = Array.from(fileList).filter((file) => file.type.startsWith("image/"));
    setQueued(images);
  }

  async function submit() {
    if (queued.length === 0) return;
    await onUpload(queued);
  }

  return (
    <section className="border-b border-federal-line bg-white">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[1.25fr_0.75fr] lg:px-6">
        <div
          className={`flex min-h-52 cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed px-6 py-8 text-center transition ${
            dragging ? "border-federal-blue bg-blue-50" : "border-federal-line bg-federal-mist"
          }`}
          role="button"
          tabIndex={0}
          aria-label="Upload alcohol label images"
          onClick={() => inputRef.current?.click()}
          onDragOver={(event: DragEvent<HTMLDivElement>) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event: DragEvent<HTMLDivElement>) => {
            event.preventDefault();
            setDragging(false);
            addFiles(event.dataTransfer.files);
          }}
        >
          <UploadCloud className="mb-3 h-10 w-10 text-federal-blue" aria-hidden="true" />
          <h2 className="text-lg font-semibold text-federal-ink">Upload label images</h2>
          <p className="mt-1 max-w-xl text-sm text-slate-600">
            Drag and drop one or more label photos, or select files from your computer.
          </p>
          <input
            ref={inputRef}
            className="sr-only"
            type="file"
            accept="image/*"
            multiple
            onChange={(event: ChangeEvent<HTMLInputElement>) => addFiles(event.target.files)}
          />
        </div>

        <div className="rounded border border-federal-line bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Batch Queue</h3>
            <span className="text-sm text-slate-500">{queued.length} file(s)</span>
          </div>
          <div className="max-h-36 space-y-2 overflow-auto" aria-live="polite">
            {queued.length === 0 ? (
              <p className="text-sm text-slate-500">No files selected.</p>
            ) : (
              queued.map((file) => (
                <div key={`${file.name}-${file.size}`} className="flex items-center gap-2 rounded border border-slate-200 px-3 py-2 text-sm">
                  <FileImage className="h-4 w-4 text-federal-blue" aria-hidden="true" />
                  <span className="min-w-0 flex-1 truncate">{file.name}</span>
                  <span className="text-slate-500">{Math.ceil(file.size / 1024)} KB</span>
                </div>
              ))
            )}
          </div>
          <button
            className="mt-4 w-full rounded bg-federal-blue px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={busy || queued.length === 0}
            onClick={submit}
          >
            {busy ? "Processing labels..." : "Process Batch"}
          </button>
        </div>
      </div>
    </section>
  );
}
