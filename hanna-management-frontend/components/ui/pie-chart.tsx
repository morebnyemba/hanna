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
  return (
    <ChartContainer
      ref={ref}
      config={{}}
      className={cn("w-full h-[300px]", className)}
      {...props}
    >
      <ResponsiveContainer>
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
