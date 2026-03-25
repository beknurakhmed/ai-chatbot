"use client";

const BUILDINGS = [
  { num: 1, name: "Entrance Gate", desc: "Main entry to campus", color: "bg-gray-500" },
  { num: 2, name: "A Block", desc: "Lesson rooms, Library", color: "bg-blue-500" },
  { num: 3, name: "B Block", desc: "Administration, Lesson rooms", color: "bg-emerald-500" },
  { num: 4, name: "C Block", desc: "Canteen, Conference Hall, Sports Hall", color: "bg-orange-500" },
  { num: 5, name: "Dormitory", desc: "Student housing", color: "bg-purple-500" },
  { num: 6, name: "Parking lot", desc: "Vehicle parking", color: "bg-pink-500" },
];

export default function CampusMap() {
  return (
    <div className="mt-3 space-y-3">
      {/* Map image */}
      <img
        src="/campus/map.jpg"
        alt="AUT Campus Map"
        className="w-full rounded-xl border border-blue-100 shadow-sm"
      />

      {/* Legend */}
      <div className="grid grid-cols-2 gap-1.5">
        {BUILDINGS.map((b) => (
          <div key={b.num} className="flex items-center gap-2 text-xs">
            <span
              className={`${b.color} text-white w-5 h-5 rounded-md flex items-center justify-center font-bold text-[10px] flex-shrink-0`}
            >
              {b.num}
            </span>
            <div className="min-w-0">
              <span className="font-semibold text-gray-800">{b.name}</span>
              <span className="text-gray-400 ml-1">— {b.desc}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
