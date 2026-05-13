"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { searchByText, searchByImage, getRandomArtworks, type ArtworkResult } from "@/lib/api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ArtworkResult[]>([]);
  const [discover, setDiscover] = useState<ArtworkResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getRandomArtworks(24).then(r => setDiscover(r.results)).catch(() => {});
  }, []);

  async function runSearch(q: string, file: File | null) {
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const response = file ? await searchByImage(file) : await searchByText(q);
      setResults(response.results);
    } catch {
      setError("Search failed — is the API running on :8000?");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault();
    if (!query.trim() && !imageFile) return;
    runSearch(query, imageFile);
  }

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const preview = URL.createObjectURL(file);
    setImageFile(file);
    setImagePreview(preview);
    setQuery("");
    runSearch("", file);
  }

  function clearImage() {
    setImageFile(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  const hasResults = results.length > 0;

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: "#FAF8F4", color: "#1C1917" }}
    >
      {/* Header */}
      <header
        className="px-6 py-4 flex items-center justify-between"
        style={{ borderBottom: "1px solid #E5DDD3" }}
      >
        <span
          style={{
            fontFamily: "var(--font-cormorant), Georgia, serif",
            fontStyle: "italic",
            fontWeight: 600,
            fontSize: "1.625rem",
            color: "#1C1917",
            letterSpacing: "-0.01em",
          }}
        >
          Sift
        </span>
        <span
          style={{
            fontFamily: "var(--font-inter), system-ui, sans-serif",
            fontSize: "0.75rem",
            color: "#6B5B4E",
          }}
        >
          Harvard Art Museums
        </span>
      </header>

      {/* Search section */}
      <div
        className={`px-6 transition-all duration-300 ${searched ? "py-5" : "py-16"}`}
      >
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div
            className="flex items-end gap-4 pb-3"
            style={{ borderBottom: "1px solid #1C1917" }}
          >
            {imagePreview ? (
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <img
                  src={imagePreview}
                  alt=""
                  className="h-8 w-8 object-cover rounded-sm flex-shrink-0"
                />
                <span
                  className="flex-1 truncate"
                  style={{
                    fontFamily: "var(--font-inter), system-ui, sans-serif",
                    fontSize: "0.875rem",
                    color: "#9C8575",
                  }}
                >
                  searching by image
                </span>
                <button
                  type="button"
                  onClick={clearImage}
                  className="flex-shrink-0"
                  style={{
                    color: "#9C8575",
                    fontSize: "1.375rem",
                    lineHeight: 1,
                    cursor: "pointer",
                    background: "none",
                    border: "none",
                  }}
                >
                  ×
                </button>
              </div>
            ) : (
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="search artworks..."
                className="flex-1 bg-transparent outline-none search-input"
                style={{
                  fontFamily: "var(--font-cormorant), Georgia, serif",
                  fontStyle: "italic",
                  fontSize: "clamp(2.5rem, 5vw, 4.5rem)",
                  color: "#1C1917",
                  lineHeight: 1.1,
                }}
              />
            )}

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              title="Search by image"
              className="flex-shrink-0"
              style={{
                color: "#9C8575",
                cursor: "pointer",
                background: "none",
                border: "none",
                padding: 0,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#8B6F47")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#9C8575")}
            >
              <CameraIcon />
            </button>

            <button
              type="submit"
              disabled={loading}
              className="flex-shrink-0"
              style={{
                color: "#9C8575",
                cursor: loading ? "default" : "pointer",
                background: "none",
                border: "none",
                padding: 0,
              }}
              onMouseEnter={(e) =>
                !loading && (e.currentTarget.style.color = "#1C1917")
              }
              onMouseLeave={(e) => (e.currentTarget.style.color = "#9C8575")}
            >
              {loading ? <SpinnerIcon /> : <SearchIcon />}
            </button>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
          />
        </form>

        {!searched && (
          <p
            className="max-w-3xl mx-auto"
            style={{
              fontFamily: "var(--font-cormorant), Georgia, serif",
              fontStyle: "italic",
              fontWeight: 400,
              fontSize: "1.25rem",
              color: "#4A3D34",
              marginTop: "14px",
            }}
          >
            Find artwork that speaks to your writing.
          </p>
        )}

        {error && (
          <p
            className="mt-4 text-center"
            style={{
              fontFamily: "var(--font-inter), system-ui, sans-serif",
              fontSize: "0.8125rem",
              color: "#8B6F47",
            }}
          >
            {error}
          </p>
        )}
      </div>

      {/* Results / discover grid */}
      {(hasResults || discover.length > 0) && (
        <div className="px-6 pb-16">
          {searched && (
            <p
              className="mb-6"
              style={{
                fontFamily: "var(--font-inter), system-ui, sans-serif",
                fontSize: "0.75rem",
                color: "#9C8575",
              }}
            >
              {results.length} results
            </p>
          )}
          {!searched && discover.length > 0 && (
            <p
              className="mb-6"
              style={{
                fontFamily: "var(--font-inter), system-ui, sans-serif",
                fontSize: "0.75rem",
                color: "#9C8575",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              Discover
            </p>
          )}
          <MasonryGrid results={searched ? results : discover} />
        </div>
      )}

      {/* Empty state after search with no results */}
      {searched && !loading && !hasResults && !error && (
        <div className="px-6 py-12 text-center">
          <p
            style={{
              fontFamily: "var(--font-cormorant), Georgia, serif",
              fontStyle: "italic",
              fontSize: "1.125rem",
              color: "#9C8575",
            }}
          >
            No artworks found.
          </p>
        </div>
      )}
    </div>
  );
}

function MasonryGrid({ results }: { results: ArtworkResult[] }) {
  const withImages = results.filter((r) => r.primary_image_url);
  return (
    <div className="masonry-grid" style={{ columns: 2, gap: "12px" }}>
      <style>{`
        @media (min-width: 640px)  { .masonry-grid { columns: 3 !important; } }
        @media (min-width: 1024px) { .masonry-grid { columns: 4 !important; } }
        @media (min-width: 1400px) { .masonry-grid { columns: 5 !important; } }
      `}</style>
      {withImages.map((artwork) => (
        <ArtworkCard key={artwork.id} artwork={artwork} />
      ))}
    </div>
  );
}

function ArtworkCard({ artwork }: { artwork: ArtworkResult }) {
  return (
    <Link
      href={`/artwork/${artwork.id}`}
      className="block"
      style={{ marginBottom: "12px", breakInside: "avoid" }}
    >
      <img
        src={artwork.primary_image_url!}
        alt={artwork.title ?? ""}
        loading="lazy"
        className="w-full h-auto block"
        style={{ display: "block", transition: "opacity 0.15s" }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.88")}
        onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
      />
      <div style={{ paddingTop: "8px" }}>
        <p
          style={{
            fontFamily: "var(--font-cormorant), Georgia, serif",
            fontSize: "0.9375rem",
            color: "#1C1917",
            lineHeight: 1.35,
            margin: 0,
          }}
        >
          {artwork.title ?? "Untitled"}
        </p>
        {(artwork.artist_name || artwork.dated) && (
          <p
            style={{
              fontFamily: "var(--font-inter), system-ui, sans-serif",
              fontSize: "0.75rem",
              color: "#9C8575",
              marginTop: "2px",
              margin: "2px 0 0",
            }}
          >
            {[artwork.artist_name, artwork.dated].filter(Boolean).join(", ")}
          </p>
        )}
      </div>
    </Link>
  );
}

function SearchIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.35-4.35" />
    </svg>
  );
}

function CameraIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3" />
    </svg>
  );
}

function SpinnerIcon() {
  return (
    <svg
      className="animate-spin"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
