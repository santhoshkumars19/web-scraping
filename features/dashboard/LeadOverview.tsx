"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from "recharts";

export interface DashboardCategorySummary {
  category: string;
  leads: number;
  color?: string | null;
}

export interface DashboardLocationSummary {
  location: string;
  leads: number;
}

interface LeadOverviewProps {
  categories?: DashboardCategorySummary[];
  locations?: DashboardLocationSummary[];
  loading?: boolean;
}

const DEFAULT_PALETTE = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626", "#0891B2"];

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

function CustomBarTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-border bg-white px-3 py-2 shadow-md text-xs">
      <p className="font-semibold text-foreground tracking-tight">{label}</p>
      <p className="text-muted-foreground mt-0.5">
        {payload[0].value.toLocaleString()} leads
      </p>
    </div>
  );
}

function CustomPieTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-border bg-white px-3 py-2 shadow-md text-xs">
      <p className="font-semibold text-foreground tracking-tight">{payload[0].name}</p>
      <p className="text-muted-foreground mt-0.5">
        {payload[0].value.toLocaleString()} leads
      </p>
    </div>
  );
}

// ─── Category Chart (Pie) ─────────────────────────────────────────────────────

function CategoryPieChart({ data, loading }: { data?: DashboardCategorySummary[]; loading?: boolean }) {
  const chartData = (data && data.length > 0) ? data : [];

  return (
    <div className="rounded-2xl border border-border bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold tracking-tight text-foreground">Leads by Category</h3>
      <p className="mt-0.5 text-xs text-muted-foreground">
        Distribution across business categories
      </p>

      <div className="mt-4 h-52">
        {loading ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            Loading categories…
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            No category distribution data yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="leads"
                nameKey="category"
                cx="40%"
                cy="50%"
                outerRadius={80}
                innerRadius={48}
                paddingAngle={2}
              >
                {chartData.map((entry, idx) => (
                  <Cell key={entry.category} fill={entry.color || DEFAULT_PALETTE[idx % DEFAULT_PALETTE.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomPieTooltip />} />
              <Legend
                layout="vertical"
                align="right"
                verticalAlign="middle"
                iconType="circle"
                iconSize={8}
                formatter={(value) => (
                  <span className="text-xs text-muted-foreground">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ─── Location Chart (Bar) ─────────────────────────────────────────────────────

function LocationBarChart({ data, loading }: { data?: DashboardLocationSummary[]; loading?: boolean }) {
  const chartData = (data && data.length > 0) ? data : [];

  return (
    <div className="rounded-2xl border border-border bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold tracking-tight text-foreground">Leads by Location</h3>
      <p className="mt-0.5 text-xs text-muted-foreground">
        Top cities by discovered leads
      </p>

      <div className="mt-4 h-52">
        {loading ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            Loading locations…
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            No location distribution data yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 0, right: 8, bottom: 0, left: 0 }}
              barSize={16}
            >
              <XAxis
                type="number"
                tick={{ fontSize: 10, fill: "#8A877E" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) =>
                  v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)
                }
              />
              <YAxis
                type="category"
                dataKey="location"
                tick={{ fontSize: 11, fill: "#5C5A53" }}
                tickLine={false}
                axisLine={false}
                width={72}
              />
              <Tooltip
                content={<CustomBarTooltip />}
                cursor={{ fill: "#F4F3EA" }}
              />
              <Bar dataKey="leads" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={entry.location}
                    fill={index === 0 ? "#BE0B31" : "#D4CEC3"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

// ─── Exported composite component ─────────────────────────────────────────────

export function LeadOverview({ categories, locations, loading }: LeadOverviewProps) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <CategoryPieChart data={categories} loading={loading} />
      <LocationBarChart data={locations} loading={loading} />
    </div>
  );
}
