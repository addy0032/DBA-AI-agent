"use client";

import ReactECharts from "echarts-for-react";
import { MetricSnapshot } from "@/types";
import { format } from "date-fns";

interface LineChartProps {
    history: MetricSnapshot[];
}

export function LineChart({ history }: LineChartProps) {
    // Use 'dark' or empty depending on user preference, but let's default to basic colors
    // that look good in both for simplicity, or we can just read CSS vars.

    const timestamps = history.map((s) => format(new Date(s.timestamp), "HH:mm:ss"));
    const activeSessions = history.map((s) => s.active_sessions_count);
    const topWaits = history.map((s) => s.top_wait_stats[0]?.wait_time_ms || 0);

    const option = {
        tooltip: {
            trigger: "axis",
            backgroundColor: "rgba(0,0,0,0.8)",
            textStyle: { color: "#fff" },
            borderWidth: 0,
        },
        legend: {
            data: ["Active Sessions", "Top Wait (ms)"],
            textStyle: { color: "#888" },
            bottom: 0,
        },
        grid: { left: "3%", right: "4%", bottom: "10%", top: "5%", containLabel: true },
        xAxis: {
            type: "category",
            boundaryGap: false,
            data: timestamps,
            axisLine: { lineStyle: { color: "#555" } },
            axisLabel: { color: "#888" },
        },
        yAxis: [
            {
                type: "value",
                name: "Sessions",
                position: "left",
                axisLine: { show: true, lineStyle: { color: "#555" } },
                axisLabel: { color: "#888" },
                splitLine: { lineStyle: { color: "#333", type: "dashed" } },
            },
            {
                type: "value",
                name: "Wait (ms)",
                position: "right",
                axisLine: { show: true, lineStyle: { color: "#555" } },
                axisLabel: { color: "#888" },
                splitLine: { show: false },
            },
        ],
        series: [
            {
                name: "Active Sessions",
                type: "line",
                smooth: true,
                data: activeSessions,
                itemStyle: { color: "#3b82f6" }, // blue-500
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.3)' }, { offset: 1, color: 'rgba(59,130,246,0)' }]
                    }
                }
            },
            {
                name: "Top Wait (ms)",
                type: "line",
                smooth: true,
                yAxisIndex: 1,
                data: topWaits,
                itemStyle: { color: "#f59e0b" }, // amber-500
            },
        ],
    };

    return <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />;
}
