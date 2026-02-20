import { MetricSnapshot } from "@/types";
import { Card, CardHeader, CardTitle, CardContent } from "../shared/Card";
import { LineChart } from "./LineChart";
import { DonutChart } from "./DonutChart";
import { BarChart } from "./BarChart";

interface LiveMetricsPanelProps {
    history: MetricSnapshot[];
    current: MetricSnapshot | null;
}

export function LiveMetricsPanel({ history, current }: LiveMetricsPanelProps) {
    if (!current || history.length === 0) return null;

    return (
        <div className="grid gap-4 md:grid-cols-12">
            <Card className="md:col-span-8 flex flex-col">
                <CardHeader>
                    <CardTitle>System Performance Trends</CardTitle>
                </CardHeader>
                <CardContent className="flex-1 min-h-[300px]">
                    <LineChart history={history} />
                </CardContent>
            </Card>

            <div className="flex flex-col gap-4 md:col-span-4">
                <Card className="flex-1 flex flex-col">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Wait Types Distribution</CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 min-h-[150px]">
                        <DonutChart data={current.top_wait_stats} />
                    </CardContent>
                </Card>

                <Card className="flex-1 flex flex-col">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Top 5 Expensive Queries</CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 min-h-[150px] -ml-4">
                        <BarChart data={current.expensive_queries} />
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
