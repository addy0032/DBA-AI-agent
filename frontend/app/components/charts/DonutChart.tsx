"use client";

import ReactECharts from "echarts-for-react";
import { WaitStatSummary } from "@/types";

interface DonutChartProps {
    data: WaitStatSummary[];
}

export function DonutChart({ data }: DonutChartProps) {
    const chartData = data.slice(0, 5).map(w => ({
        name: w.wait_type,
        value: w.wait_time_ms
    }));

    const option = {
        tooltip: {
            trigger: "item",
            formatter: "{b}: {c}ms ({d}%)",
            backgroundColor: "rgba(0,0,0,0.8)",
            textStyle: { color: "#fff" },
            borderWidth: 0,
        },
        legend: {
            show: false
        },
        series: [
            {
                type: "pie",
                radius: ["40%", "70%"],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 4,
                    borderColor: "rgba(0,0,0,0.1)",
                    borderWidth: 2
                },
                label: {
                    show: true,
                    position: "outside",
                    formatter: "{b}\n{d}%",
                    color: "#888"
                },
                data: chartData,
            }
        ]
    };

    return <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />;
}
