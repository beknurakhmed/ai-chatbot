"use client";

import type { StaffMember } from "@/lib/store";

interface Props {
  staff: StaffMember[];
}

export default function StaffCard({ staff }: Props) {
  return (
    <div className="flex flex-col gap-3 mt-3">
      {staff.map((s) => (
        <div
          key={s.name}
          className="flex items-center gap-4 bg-gradient-to-r from-blue-50 to-white rounded-2xl p-4 border border-blue-100 shadow-sm"
        >
          {s.photo ? (
            <img
              src={s.photo}
              alt={s.name}
              className="w-20 h-20 rounded-2xl object-cover border-2 border-blue-200 shadow-md flex-shrink-0"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          ) : (
            <div className="w-20 h-20 rounded-2xl bg-blue-200 flex items-center justify-center text-blue-600 font-bold text-2xl border-2 border-blue-100 flex-shrink-0">
              {s.name.charAt(0)}
            </div>
          )}
          <div className="min-w-0">
            <div className="text-base font-bold text-gray-800">
              {s.name}
            </div>
            <div className="text-sm text-blue-600 mt-0.5">
              {s.position}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
