"use client"

import * as React from "react"
import { Bar, BarChart as RechartsBarChart, ResponsiveContainer } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  ChartConfig,
} from "@/components/ui/chart"
import { cn } from "@/lib/utils"

const BarChart = React.forwardRef<
  HTMLDivElement,
  {
    data: any[]
    config: ChartConfig
    className?: string
    layout?: "horizontal" | "vertical"
  }
>(({ data, config, className, layout = "horizontal", ...props }, ref) => {
  if (!data || data.length === 0) {
    return (
      <div className={cn("w-full h-full flex items-center justify-center text-gray-400 text-sm", className)}>
        No data available
      </div>
    )
  }

  return (
    <ChartContainer
      ref={ref}
      config={config}
      className={cn("w-full", className)}
      {...props}
    >
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart data={data} layout={layout}>
          <ChartTooltip content={<ChartTooltipContent />} />
          <ChartLegend content={<ChartLegendContent />} />
          {Object.entries(config).map(([key, itemConfig]) => {
            if (itemConfig.type === "bar") {
              return <Bar key={key} dataKey={key} fill={itemConfig.color} />
            }
            return null
          })}
        </RechartsBarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
})
BarChart.displayName = "BarChart"

export { BarChart }