#!/usr/bin/env python3
"""
draft_email.py — produce the daily client email exactly matching the
format the team uses today.

Output:
  * .html   — rich body for paste into Gmail
  * .txt    — plain-text fallback
  * .eml    — opens in default mail client with To/Cc/Subject/Body/Attachment

Usage:
    python draft_email.py \\
        --export /path/to/Daily Post Export - 2026-05-26.xlsx \\
        --memory-bank /path/to/memory_bank.csv \\
        --client-xlsx "client-sharable/LF _ Amazon - Boostable Posts [05.26.26].xlsx" \\
        --reporting-date 2026-05-26 \\
        --output "client-sharable/email_draft_2026-05-26" \\
        --sender-name Aaron \\
        --from-email aaron@listenfirstmedia.com \\
        [--state-dir state/]

The table in the email body mirrors the reference Aaron sends each day:
  - Columns: Brand | Title | Channel | Engagements | Engagement Rate | Benchmark Δ
  - All ORGANIC posts that are Overperforming (Δ > 0), sorted by Δ desc
  - Benchmark Δ shown as percentage (raw delta × 100)
  - Channel cells link to the post URL
  - Benchmark Δ cells get the Overperforming green (#B7E1CD)
"""
from __future__ import annotations
import argparse, sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
# Reuse the pipeline from build_client_sheet.py
from build_client_sheet import (
    load_export, load_memory_bank, dedupe_clean, enrich,
    load_benchmarks, fill_missing_benchmarks, resolve_benchmarks_path,
)

DEFAULT_TO = 'pvs-boosting-team@amazon.com'
DEFAULT_CC = ('Amazon MGM Studios Streaming <team-amazonstreaming@listenfirstmedia.com>, '
              'douglbos@amazon.com, PVSBrand-Social@amazon.com')


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--export', required=True)
    p.add_argument('--memory-bank', required=True)
    p.add_argument('--client-xlsx', required=True, help='Path to the client deliverable to attach')
    p.add_argument('--reporting-date', required=True, help='YYYY-MM-DD')
    p.add_argument('--output', required=True, help='Output basename (without extension); .html/.txt/.eml are appended')
    p.add_argument('--sender-name', default='Aaron')
    p.add_argument('--from-email', default='')
    p.add_argument('--to', default=DEFAULT_TO)
    p.add_argument('--cc', default=DEFAULT_CC)
    p.add_argument('--benchmarks')
    p.add_argument('--state-dir')
    return p.parse_args()


def build_html(rows, sender_name: str) -> str:
    """HTML body matching Aaron's format: clean, simple, with green Δ cells."""
    GREEN = '#B7E1CD'
    LINK = '#1155CC'

    table_rows = []
    for r in rows:
        delta_pct = f"{int(round(r['Benchmark Δ'] * 100))}%"
        er_pct = f"{int(round(r['ER'] * 100))}%"
        eng = f"{int(r['Engagements']):,}"
        url = r['Post Link']
        table_rows.append(
            "<tr>"
            f"<td style='padding:5px 14px;border-bottom:1px solid #e0e0e0'>{r['Brand']}</td>"
            f"<td style='padding:5px 14px;border-bottom:1px solid #e0e0e0'>{r['Title']}</td>"
            f"<td style='padding:5px 14px;border-bottom:1px solid #e0e0e0'>"
            f"<a href='{url}' style='color:{LINK};text-decoration:underline'>{r['Channel']}</a></td>"
            f"<td style='padding:5px 14px;border-bottom:1px solid #e0e0e0;text-align:right'>{eng}</td>"
            f"<td style='padding:5px 14px;border-bottom:1px solid #e0e0e0;text-align:right'>{er_pct}</td>"
            f"<td style='padding:5px 14px;border-bottom:1px solid #e0e0e0;text-align:center;background:{GREEN}'>{delta_pct}</td>"
            "</tr>"
        )

    return f"""<html><body style="font-family:Arial,sans-serif;font-size:13px;color:#222;line-height:1.5">
<p>Good morning,</p>
<p>Please see the attached post list for boosting consideration, and a summary of what's overperforming below:</p>

<table style="border-collapse:collapse;font-size:13px">
  <thead>
    <tr style="border-bottom:2px solid #222">
      <th style="padding:6px 14px;text-align:left">Brand</th>
      <th style="padding:6px 14px;text-align:left">Title</th>
      <th style="padding:6px 14px;text-align:left">Channel</th>
      <th style="padding:6px 14px;text-align:right">Engagements</th>
      <th style="padding:6px 14px;text-align:right">Engagement Rate</th>
      <th style="padding:6px 14px;text-align:right">Benchmark Δ</th>
    </tr>
  </thead>
  <tbody>
    {''.join(table_rows)}
  </tbody>
</table>

<p>Best,<br/>{sender_name}</p>
</body></html>"""


def build_plain(rows, sender_name: str) -> str:
    lines = [
        'Good morning,',
        '',
        "Please see the attached post list for boosting consideration, and a summary of what's overperforming below:",
        '',
        f'{"Brand":<16} {"Title":<32} {"Channel":<10} {"Engagements":>12} {"ER":>5} {"Benchmark Δ":>12}',
        '-' * 96,
    ]
    for r in rows:
        delta_pct = f"{int(round(r['Benchmark Δ']*100))}%"
        er_pct = f"{int(round(r['ER']*100))}%"
        lines.append(
            f"{r['Brand']:<16} {r['Title'][:32]:<32} {r['Channel']:<10} {int(r['Engagements']):>12,} {er_pct:>5} {delta_pct:>12}"
        )
    lines += ['', 'Best,', sender_name]
    return '\n'.join(lines)


def build_eml(html: str, text: str, args, attachment: Path) -> bytes:
    rd = datetime.strptime(args.reporting_date, '%Y-%m-%d').date()
    weekday = rd.strftime('%A')
    date_str = rd.strftime('%B %-d, %Y') if sys.platform != 'win32' else rd.strftime('%B %d, %Y')
    msg = EmailMessage()
    if args.from_email: msg['From'] = args.from_email
    msg['To'] = args.to
    msg['Cc'] = args.cc
    msg['Subject'] = f'Prime Video | Boostable Posts ({weekday}, {date_str})'
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')
    if attachment.exists():
        with attachment.open('rb') as f:
            msg.add_attachment(
                f.read(),
                maintype='application',
                subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                filename=attachment.name,
            )
    return bytes(msg)


def main():
    args = parse_args()
    rd = datetime.strptime(args.reporting_date, '%Y-%m-%d').date()

    raw, header = load_export(args.export)
    cleaned = dedupe_clean(raw, header)
    mb = load_memory_bank(args.memory_bank)
    bm_path = resolve_benchmarks_path(args)
    benchmarks, _ = load_benchmarks(bm_path)
    enriched = enrich(cleaned, mb, benchmarks)
    organic = [e for e in enriched if not e['Has Paid']]
    fill_missing_benchmarks(organic)

    # Aaron's email shows only OVERPERFORMING posts (Δ > 0), sorted by Δ desc
    overperformers = [e for e in organic if (e['Benchmark Δ'] or 0) > 0]
    overperformers.sort(key=lambda x: -(x['Benchmark Δ'] or 0))

    print(f'Overperforming posts to include in email: {len(overperformers)}')

    html = build_html(overperformers, args.sender_name)
    text = build_plain(overperformers, args.sender_name)
    eml = build_eml(html, text, args, Path(args.client_xlsx))

    out_base = Path(args.output)
    (out_base.with_suffix('.html')).write_text(html, encoding='utf-8')
    (out_base.with_suffix('.txt')).write_text(text, encoding='utf-8')
    (out_base.with_suffix('.eml')).write_bytes(eml)

    print(f'Wrote: {out_base.with_suffix(".html")}')
    print(f'Wrote: {out_base.with_suffix(".txt")}')
    print(f'Wrote: {out_base.with_suffix(".eml")}  (double-click to open in mail client with attachment)')


if __name__ == '__main__':
    main()
