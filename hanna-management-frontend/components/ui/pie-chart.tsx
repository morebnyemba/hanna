"use client"

import * as React from "react"
import { Pie, PieChart as RechartsPieChart, ResponsiveContainer } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart"
import { cn } from "@/lib/utils"

const PieChart = React.forwardRef<
  HTMLDivElement,
  {
    data: any[]
    className?: string
  }
>(({ data, className, ...props }, ref) => {
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
      config={{}}
      className={cn("w-full", className)}
      {...props}
    >
      <ResponsiveContainer width="100%" height="100%">
        <RechartsPieChart>
          <ChartTooltip content={<ChartTooltipContent />} />
          <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} fill="#8884d8" label />
          <ChartLegend content={<ChartLegendContent />} />
        </RechartsPieChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
})
PieChart.displayName = "PieChart"

export { PieChart }
