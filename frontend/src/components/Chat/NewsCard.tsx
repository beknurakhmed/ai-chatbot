"use client";

import { QRCodeSVG } from "qrcode.react";
import type { NewsItemData } from "@/lib/store";

interface Props {
  news: NewsItemData[];
}

export default function NewsCard({ news }: Props) {
  return (
    <div className="flex flex-col gap-3 mt-3">
      {news.map((n, i) => (
        <div
          key={i}
          className="flex items-start gap-4 bg-gradient-to-r from-amber-50 to-white rounded-2xl p-4 border border-amber-100 shadow-sm"
        >
          <div className="min-w-0 flex-1">
            <div className="text-sm font-bold text-gray-800">{n.title}</div>
            {n.date && (
              <div className="text-xs text-gray-400 mt-1">{n.date}</div>
            )}
          </div>
          {n.url && (
            <div className="flex-shrink-0 flex flex-col items-center gap-1">
              <QRCodeSVG value={n.url} size={56} level="L" />
              <span className="text-[9px] text-gray-400">Scan</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
