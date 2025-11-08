"use client"

import * as React from "react"
import {
  createContext,
  forwardRef,
  useCallback,
  useContext,
  useMemo,
} from "react"
import {
  Area,
  Bar,
  Cell,
  Dot,
  Label,
  LabelList,
  Line,
  Pie,
  PolarGrid,
  PolarRadiusAxis,
  RadialBar,
  Rectangle,
  Sector,
  Text,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts"
import {
  type AxisConfig,
  type ChartConfig,
  type ChartContainerProps,
  type ChartContextProps,
  type ChartLegendContentProps,
  type ChartStyleConfig,
  type ChartTooltipContentProps,
} from "recharts-extend"

import {
  ChartStyle,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "recharts-extend"

const ChartContainer = forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    config: ChartConfig
    children: React.ReactNode
  }
>(({ id, className, style, config, ...props }, ref) => {
  const uniqueId = useMemo(() => id || `chart-${Math.random().toString(36).slice(2)}`, [id])

  return (
    <div
      ref={ref}
      id={uniqueId}
      className={className}
      style={
        {
          ...style,
          "--chart-font-family": "var(--font-sans)",
          "--chart-font-size": "12px",
        } as React.CSSProperties
      }
      {...props}
    >
      <ChartStyle config={config} id={uniqueId} />
      {props.children}
    </div>
  )
})
ChartContainer.displayName = "ChartContainer"

const ChartContext = createContext<ChartContextProps | null>(null)

function useChart() {
  const context = useContext(ChartContext)

  if (!context) {
    throw new Error("useChart must be used within a <ChartContainer />")
  }

  return context
}

export {
  ChartContainer,
  ChartContext,
  useChart,
  ChartStyle,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  // Recharts
  Area,
  Bar,
  Cell,
  Dot,
  Label,
  LabelList,
  Line,
  Pie,
  PolarGrid,
  PolarRadiusAxis,
  RadialBar,
  Rectangle,
  Sector,
  Text,
  XAxis,
  YAxis,
  ZAxis,
}
export type {
  AxisConfig,
  ChartConfig,
  ChartContainerProps,
  ChartContextProps,
  ChartLegendContentProps,
  ChartStyleConfig,
  ChartTooltipContentProps,
}