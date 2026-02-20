"use client";

import ReactECharts from "echarts-for-react";
import { QueryStat } from "@/types";

interface BarChartProps {
    data: QueryStat[];
}

export function BarChart({ data }: BarChartProps) {
    const chartData = [...data].sort((a, b) => a.total_worker_time - b.total_worker_time).slice(-5);

    const categories = chartData.map(q => q.query_hash);
    const values = chartData.map(q => q.total_worker_time);

    const option = {
        tooltip: {
            trigger: "axis",
            axisPointer: { type: "shadow" },
            backgroundColor: "rgba(0,0,0,0.8)",
            textStyle: { color: "#fff" },
            borderWidth: 0,
        },
        grid: { left: "3%", right: "4%", bottom: "3%", top: "3%", containLabel: true },
        xAxis: {
            type: "value",
            name: "Worker Time",
            axisLine: { show: false },
            axisLabel: { color: "#888" },
            splitLine: { lineStyle: { color: "#333", type: "dashed" } },
        },
        yAxis: {
            type: "category",
            data: categories,
            axisLine: { lineStyle: { color: "#555" } },
            axisLabel: { color: "#888", fontSize: 10 },
        },
        series: [
            {
                name: "Worker Time",
                type: "bar",
                data: values,
                itemStyle: { color: "#ef4444", borderRadius: [0, 4, 4, 0] },
            }
        ]
    };

    return <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />;
}
