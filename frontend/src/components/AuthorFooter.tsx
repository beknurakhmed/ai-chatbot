"use client";

export default function AuthorFooter({ inline }: { inline?: boolean }) {
  return (
    <span
      className={inline
        ? "text-[10px] text-gray-400 font-medium"
        : "fixed z-40 bottom-4 right-6 bg-white/90 backdrop-blur-sm border border-gray-200 shadow-lg rounded-full px-5 py-2.5 text-sm text-gray-500 font-medium"
      }
    >
      {inline
        ? <>by <b>Akhmedov Beknur</b> | ECE</>
        : <>Developed by <span className="font-bold text-gray-800">Akhmedov Beknur</span> <span className="text-gray-400">| ECE</span></>
      }
    </span>
  );
}
