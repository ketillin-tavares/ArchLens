export function MarkdownStyles(): JSX.Element {
  return (
    <style>{`
    .md-body { font-family: 'Geist', sans-serif; color: #0F172A; line-height: 1.65; font-size: 15px; }
    .md-h1 { font-size: 30px; font-weight: 600; letter-spacing: -1px; color: #0A2540; margin: 0 0 20px; line-height:1.2; }
    .md-h2 { font-size: 22px; font-weight: 600; letter-spacing: -0.5px; color: #0A2540; margin: 36px 0 12px; padding-bottom: 8px; border-bottom: 1px solid #E2E8F0; }
    .md-h3 { font-size: 17px; font-weight: 600; color: #0F172A; margin: 24px 0 8px; }
    .md-p { margin: 0 0 14px; }
    .md-p a { color: #2563EB; text-decoration: none; }
    .md-p a:hover { text-decoration: underline; }
    .md-body code { font-family: 'Geist Mono', monospace; font-size: 13px; background: #F1F5F9; padding: 1px 6px; border-radius: 4px; color: #0F172A; }
    .md-pre { background: #0F172A; color: #E2E8F0; padding: 16px 20px; border-radius: 10px; overflow-x: auto; font-family: 'Geist Mono', monospace; font-size: 13px; line-height: 1.6; margin: 16px 0; }
    .md-pre code { background: none; color: inherit; padding: 0; }
    .md-ul, .md-ol { padding-left: 22px; margin: 0 0 16px; }
    .md-ul li, .md-ol li { margin: 6px 0; }
    .md-quote { border-left: 3px solid #2563EB; padding: 4px 16px; margin: 16px 0; color: #475569; font-style: italic; }
    .md-table-wrap { overflow-x: auto; margin: 16px 0; border: 1px solid #E2E8F0; border-radius: 10px; }
    .md-table { width: 100%; border-collapse: collapse; font-size: 14px; }
    .md-table th { text-align: left; font-family: 'Geist Mono', monospace; font-size: 11px; color: #64748B; letter-spacing: 1px; text-transform: uppercase; font-weight: 500; padding: 10px 16px; background: #F8FAFC; border-bottom: 1px solid #E2E8F0; }
    .md-table td { padding: 12px 16px; border-top: 1px solid #F1F5F9; }
    .md-table tr:first-child td { border-top: none; }
    .md-body strong { color: #0A2540; font-weight: 600; }
  `}</style>
  );
}
