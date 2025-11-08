"use client"

import * as React from "react"
import { Bar, BarChart as RechartsBarChart, ResponsiveContainer } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  useChart,
} from "@/components/ui/chart"
import { cn } from "@/lib/utils"

const BarChart = React.forwardRef<
  HTMLDivElement,
  {
    data: any[]
    config: any
    className?: string
  }
>(({ data, config, className, ...props }, ref) => {
  const { layout = "horizontal" } = useChart()

  return (
    <ChartContainer
      ref={ref}
      config={config}
      className={cn("w-full h-[300px]", className)}
      {...props}
    >
      <ResponsiveContainer>
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
