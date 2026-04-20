import type { JSX } from "react";
import type { RiskSeverity } from "@/types/RiskSeverity";
import { RiskCallout } from "./RiskCallout";

const RISK_PATTERN = /^>\s*\[!(risco:(critica|alta|media|baixa))\]\s*(.*)/;

interface MarkdownRendererProps {
  source: string;
}

function escapeInline(raw: string): string {
  let t = raw
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  t = t.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noreferrer">$1</a>',
  );
  return t;
}

export function MarkdownRenderer({
  source,
}: MarkdownRendererProps): JSX.Element {
  const out: JSX.Element[] = [];
  const lines = source.split("\n");
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("```")) {
      i++;
      const buf: string[] = [];
      while (i < lines.length && !lines[i].startsWith("```")) {
        buf.push(lines[i]);
        i++;
      }
      i++;
      out.push(
        <pre key={key++} className="md-pre">
          <code>{buf.join("\n")}</code>
        </pre>,
      );
      continue;
    }

    const heading = /^(#{1,3})\s+(.*)/.exec(line);
    if (heading) {
      const level = heading[1].length;
      const Tag = `h${level}` as "h1" | "h2" | "h3";
      out.push(
        <Tag
          key={key++}
          className={`md-h${level}`}
          dangerouslySetInnerHTML={{ __html: escapeInline(heading[2]) }}
        />,
      );
      i++;
      continue;
    }

    const callout = RISK_PATTERN.exec(line);
    if (callout) {
      const level = callout[2] as RiskSeverity;
      const title = callout[3];
      const body: string[] = [];
      i++;
      while (i < lines.length && lines[i].startsWith(">")) {
        body.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      out.push(
        <RiskCallout
          key={key++}
          level={level}
          title={title}
          body={body.join("\n")}
        />,
      );
      continue;
    }

    if (line.startsWith(">")) {
      const buf: string[] = [];
      while (i < lines.length && lines[i].startsWith(">")) {
        buf.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      out.push(
        <blockquote
          key={key++}
          className="md-quote"
          dangerouslySetInnerHTML={{ __html: escapeInline(buf.join(" ")) }}
        />,
      );
      continue;
    }

    if (line.includes("|") && lines[i + 1]?.includes("---")) {
      const header = line
        .split("|")
        .map((s) => s.trim())
        .filter(Boolean);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].includes("|")) {
        rows.push(
          lines[i]
            .split("|")
            .map((s) => s.trim())
            .filter(Boolean),
        );
        i++;
      }
      out.push(
        <div key={key++} className="md-table-wrap">
          <table className="md-table">
            <thead>
              <tr>
                {header.map((h, j) => (
                  <th
                    key={j}
                    dangerouslySetInnerHTML={{ __html: escapeInline(h) }}
                  />
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, j) => (
                <tr key={j}>
                  {r.map((c, k) => (
                    <td
                      key={k}
                      dangerouslySetInnerHTML={{ __html: escapeInline(c) }}
                    />
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ""));
        i++;
      }
      out.push(
        <ul key={key++} className="md-ul">
          {items.map((it, j) => (
            <li
              key={j}
              dangerouslySetInnerHTML={{ __html: escapeInline(it) }}
            />
          ))}
        </ul>,
      );
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ""));
        i++;
      }
      out.push(
        <ol key={key++} className="md-ol">
          {items.map((it, j) => (
            <li
              key={j}
              dangerouslySetInnerHTML={{ __html: escapeInline(it) }}
            />
          ))}
        </ol>,
      );
      continue;
    }

    if (line.trim()) {
      const buf = [line];
      i++;
      while (
        i < lines.length &&
        lines[i].trim() &&
        !/^(#|>|```|[-*]\s|\d+\.\s)/.test(lines[i]) &&
        !lines[i].includes("|")
      ) {
        buf.push(lines[i]);
        i++;
      }
      out.push(
        <p
          key={key++}
          className="md-p"
          dangerouslySetInnerHTML={{ __html: escapeInline(buf.join(" ")) }}
        />,
      );
      continue;
    }

    i++;
  }

  return <>{out}</>;
}
