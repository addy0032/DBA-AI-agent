import { Loader2 } from "lucide-react";

export function Loader({ size = 24, className = "" }: { size?: number, className?: string }) {
    return (
        <Loader2
            size={size}
            className={`animate-spin text-zinc-500 dark:text-zinc-400 ${className}`}
        />
    );
}

export function FullPageLoader() {
    return (
        <div className="flex h-screen w-full items-center justify-center bg-zinc-50 dark:bg-black">
            <div className="flex flex-col items-center gap-4">
                <Loader size={48} />
                <p className="text-zinc-500 dark:text-zinc-400 font-medium">Connecting to DBA Agent...</p>
            </div>
        </div>
    );
}
