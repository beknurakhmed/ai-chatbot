"use client";

import type { TimetableLesson } from "@/lib/store";

const DAY_ORDER = ["Mo", "Tu", "We", "Th", "Fr"];
const DAY_NAMES: Record<string, string> = {
  Mo: "Mon",
  Tu: "Tue",
  We: "Wed",
  Th: "Thu",
  Fr: "Fri",
};
const DAY_COLORS: Record<string, string> = {
  Mo: "bg-blue-500",
  Tu: "bg-emerald-500",
  We: "bg-purple-500",
  Th: "bg-orange-500",
  Fr: "bg-pink-500",
};

interface Props {
  group: string;
  lessons: TimetableLesson[];
}

export default function TimetableView({ group, lessons }: Props) {
  // Group by day
  const byDay: Record<string, TimetableLesson[]> = {};
  for (const l of lessons) {
    if (!byDay[l.day]) byDay[l.day] = [];
    byDay[l.day].push(l);
  }

  return (
    <div className="w-full overflow-x-auto">
      <div className="text-sm font-bold text-blue-600 mb-2 text-center">
        {group}
      </div>
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-blue-50">
            <th className="px-2 py-1.5 text-left font-semibold text-gray-500 border-b border-blue-100 w-12">Day</th>
            <th className="px-2 py-1.5 text-left font-semibold text-gray-500 border-b border-blue-100 w-16">Time</th>
            <th className="px-2 py-1.5 text-left font-semibold text-gray-500 border-b border-blue-100">Subject</th>
            <th className="px-2 py-1.5 text-left font-semibold text-gray-500 border-b border-blue-100 hidden sm:table-cell">Teacher</th>
            <th className="px-2 py-1.5 text-left font-semibold text-gray-500 border-b border-blue-100 w-14">Room</th>
          </tr>
        </thead>
        <tbody>
          {DAY_ORDER.map((day) => {
            const dayLessons = byDay[day];
            if (!dayLessons) return null;

            return dayLessons.map((l, i) => (
              <tr
                key={`${day}-${i}`}
                className="border-b border-gray-50 hover:bg-blue-50/50 transition-colors"
              >
                {/* Day label — only on first row of each day */}
                {i === 0 ? (
                  <td
                    className="px-2 py-1.5 align-top"
                    rowSpan={dayLessons.length}
                  >
                    <span
                      className={`inline-block px-1.5 py-0.5 rounded text-white text-[10px] font-bold ${DAY_COLORS[day] || "bg-gray-400"}`}
                    >
                      {DAY_NAMES[day] || day}
                    </span>
                  </td>
                ) : null}
                <td className="px-2 py-1.5 text-gray-500 whitespace-nowrap">
                  {l.time.split("-")[0]}
                </td>
                <td className="px-2 py-1.5 font-medium text-gray-800">
                  {l.subject}
                </td>
                <td className="px-2 py-1.5 text-gray-500 hidden sm:table-cell">
                  {l.teacher}
                </td>
                <td className="px-2 py-1.5 text-gray-500 font-mono">
                  {l.room}
                </td>
              </tr>
            ));
          })}
        </tbody>
      </table>
    </div>
  );
}
