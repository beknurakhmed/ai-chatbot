"use client";

import { useEffect, useState } from "react";
import { fetchBuildings, type BuildingData } from "@/lib/api";

export default function CampusMap() {
  const [buildings, setBuildings] = useState<BuildingData[]>([]);
  const [mapImage, setMapImage] = useState("/campus/map.jpg");

  useEffect(() => {
    fetchBuildings().then((all) => {
      // num=0 is the campus map image
      const mapEntry = all.find((b) => b.num === 0);
      if (mapEntry?.photo) setMapImage(mapEntry.photo);
      setBuildings(all.filter((b) => b.num > 0));
    });
  }, []);

  return (
    <div className="mt-3 space-y-3">
      {/* Map image from DB */}
      <img
        src={mapImage}
        alt="AUT Campus Map"
        className="w-full rounded-xl border border-blue-100 shadow-sm"
      />

      {/* Legend from DB */}
      {buildings.length > 0 && (
        <div className="grid grid-cols-2 gap-1.5">
          {buildings.map((b) => (
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
      )}
    </div>
  );
}
